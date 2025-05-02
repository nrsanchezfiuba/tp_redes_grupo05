local my_protocol = Proto("tp1_redes", "Protocolo TP1 Redes")

local conversation = {}

local fields = {
    ProtoField.uint8("tp1_redes.flags.prt", "PRT Flag", base.DEC, nil, 0xC000),
    ProtoField.bool("tp1_redes.flags.mod", "MOD Flag", 16, nil, 0x2000),
    ProtoField.bool("tp1_redes.flags.syn", "SYN Flag", 16, nil, 0x1000),
    ProtoField.bool("tp1_redes.flags.fin", "FIN Flag", 16, nil, 0x0800),
    ProtoField.bool("tp1_redes.flags.ack", "ACK Flag", 16, nil, 0x0400),
    ProtoField.uint16("tp1_redes.length", "Length", base.DEC, nil, 0x03FF),
    ProtoField.uint16("tp1_redes.seq_num", "Sequence Number", base.DEC),
    ProtoField.uint16("tp1_redes.ack_num", "ACK Number", base.DEC),
    ProtoField.string("tp1_redes.data", "Data", base.STRING)
}

my_protocol.fields = fields

function my_protocol.dissector(tvbuf, pinfo, tree)
    if tvbuf:len() < 6 then
        pinfo.cols.info:set("Paquete demasiado corto")
        return {}
    end

    local data_length = bit.band(tvbuf(0, 2):uint(), 0x03FF)
    local total_length = 6 + data_length

    if data_length > 1024 then
        pinfo.cols.info:set(string.format("Longitud inválida: %d (>1024)", data_length))
        return {}
    end

    if tvbuf:len() < total_length then
        pinfo.cols.info:set(string.format("Truncado (esperados %d bytes)", total_length))
        return {}
    end

    local subtree = tree:add(my_protocol, tvbuf(0, total_length), string.format("TP1 Redes (%d bytes)", total_length))

    local flags_and_length = tvbuf(0, 2):uint()

    local flags_subtree = subtree:add("Flags")
    flags_subtree:add(fields[1], tvbuf(0, 2)) -- PRT
    flags_subtree:add(fields[2], tvbuf(0, 2)) -- MOD
    flags_subtree:add(fields[3], tvbuf(0, 2)) -- SYN
    flags_subtree:add(fields[4], tvbuf(0, 2)) -- FIN
    flags_subtree:add(fields[5], tvbuf(0, 2)) -- ACK

    subtree:add(fields[6], tvbuf(0, 2))      -- Length
    subtree:add(fields[7], tvbuf(2, 2))      -- Seq Num
    subtree:add(fields[8], tvbuf(4, 2))      -- ACK Num

    if data_length > 0 then
        local data = tvbuf(6, data_length)
        subtree:add(fields[9], data)
    end

    local protocol_byte = bit.rshift(bit.band(flags_and_length, 0xC000), 14)
    local protocol_name = "Invalid protocol"

    if protocol_byte == 0 then
        protocol_name = "SW"
    elseif protocol_byte == 1 then
        protocol_name = "GBN"
    end

    local len = bit.band(flags_and_length, 0x03FF)
    local seq = tvbuf(2, 2):uint()
    local ack = tvbuf(4, 2):uint()

    -- Configurar columna de información
    local info = string.format("%d -> %d Len=%d,Seq=%d,Ack=%d [Protocol: %s]",
        pinfo.src_port,
        pinfo.dst_port,
        len,
        seq,
        ack,
        protocol_name
    )
    pinfo.cols.protocol = my_protocol.name
    pinfo.cols.info:set(info)

    return {
        total_length = total_length,
        data_length = data_length,
        flow = {
            src_port = pinfo.src_port,
            dst_port = pinfo.dst_port
        }
    }
end

local function heuristic(buf, pkt, root)
    local ret = my_protocol.dissector(buf, pkt, root)

    if type(ret) ~= "table" or ret["total_length"] < 6 then
        return false
    end

    if ret["data_length"] > 1024 then
        return false
    end

    if ret["flow"]["dst_port"] == 2357 then
        conversation[ret["flow"]["src_port"]] = true
        return true
    elseif conversation[ret["flow"]["dst_port"]] then
        conversation[ret["flow"]["src_port"]] = true
        return true
    end

    return false
end

my_protocol:register_heuristic("udp", heuristic)

local udp_table = DissectorTable.get("udp.port")
udp_table:add(2357, my_protocol)

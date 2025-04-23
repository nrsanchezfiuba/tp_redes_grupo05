from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Node
from mininet.topo import Topo
from typing import Any, cast


class LinuxRouter(Node):
    def config(self, *args: Any, **kwargs: Any) -> dict:
        result = super().config(*args, **kwargs)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")
        return result

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


class FragmentationTopo(Topo):
    def build(self, **_opts):
        r1 = self.addNode("r1", cls=LinuxRouter, ip=None)
        s1, s2 = [self.addSwitch(s) for s in ("s1", "s2")]

        self.addLink(s1, r1, intfName2="r1-eth1",
                     params2={"ip": "10.0.0.1/30"})
        self.addLink(s2, r1, intfName2="r1-eth2",
                     params2={"ip": "10.0.0.5/30"})

        h1 = self.addHost("h1", ip="10.0.0.2/30", defaultRoute="via 10.0.0.1")
        h2 = self.addHost("h2", ip="10.0.0.6/30", defaultRoute="via 10.0.0.5")

        for h, s in [(h1, s1), (h2, s2)]:
            self.addLink(h, s)


def run():
    topo = FragmentationTopo()
    net = Mininet(topo=topo)
    net.start()

    r1 = cast(Node, net.get("r1"))
    h1 = cast(Node, net.get("h1"))
    h2 = cast(Node, net.get("h2"))

    # Set r1-s2 MTU to 600 bytes
    r1.cmd("ifconfig r1-eth2 mtu 600")

    # Unset DF bit
    h1.cmd("sysctl -w net.ipv4.ip_no_pmtu_disc=1")
    h2.cmd("sysctl -w net.ipv4.ip_no_pmtu_disc=1")

    # Disable TCP MTU probing
    h1.cmd("sysctl -w net.ipv4.tcp_mtu_probing=0")
    h2.cmd("sysctl -w net.ipv4.tcp_mtu_probing=0")

    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    run()

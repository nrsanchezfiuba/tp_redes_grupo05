from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.topo import Topo


class MyTopo(Topo):  # type: ignore
    def build(self) -> None:
        # Crear switches
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        s3 = self.addSwitch("s3")

        # Crear hosts
        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")

        # test
        # Conectar hosts a switches
        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, s3, intfParams={"s2-eth2": {"mtu": 200}})
        self.addLink(s3, h2, loss=10)


def run() -> None:
    topo = MyTopo()
    net = Mininet(
        topo=topo,
        link=TCLink,
        switch=OVSKernelSwitch,
        controller=None,
        autoSetMacs=True,
    )
    net.start()

    print("Topología iniciada con switches en modo standalone.")
    CLI(net)
    net.stop()


topos = {"mytopo": (lambda: MyTopo())}

if __name__ == "__main__":
    setLogLevel("info")
    run()

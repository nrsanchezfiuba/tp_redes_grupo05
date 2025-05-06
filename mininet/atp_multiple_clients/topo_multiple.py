import sys
from typing import Any

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo


class SingleClientTopo(Topo):  # type: ignore
    def __init__(self, custom_loss: float, **opts: Any) -> None:
        self.custom_loss = custom_loss
        super().__init__(**opts)

    def build(self, **_opts: Any) -> None:
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")

        s1 = self.addSwitch("s1")

        self.addLink(h1, s1, cls=TCLink, loss=self.custom_loss)
        self.addLink(h2, s1)
        self.addLink(h3, s1)


def run(loss: float) -> None:
    topo = SingleClientTopo(loss)
    net = Mininet(topo=topo)
    net.start()
    CLI(net)
    net.stop()


if __name__ == "__main__":
    setLogLevel("info")
    loss = 0.0
    if len(sys.argv) > 2 and sys.argv[1] == "--loss":
        loss = float(sys.argv[2]) / 2.0
    run(loss)

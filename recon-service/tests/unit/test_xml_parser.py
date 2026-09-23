"""
Unit Tests — XML Parser
=======================
Tests for app/scanner/xml_parser.py

All tests use inline XML strings — no Nmap, no Docker, no network required.
"""

import pytest

from app.scanner.xml_parser import XmlParseError, parse_nmap_xml


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_nmaprun(*host_blocks: str) -> str:
    """Wrap host XML blocks in a minimal nmaprun envelope."""
    hosts = "\n".join(host_blocks)
    return f"""<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sV -oX - 172.20.0.0/24"
         version="7.94" xmloutputversion="1.05">
  {hosts}
  <runstats>
    <finished time="1727000060" elapsed="60"/>
    <hosts up="1" down="0" total="1"/>
  </runstats>
</nmaprun>"""


def _make_host(
    ip: str = "172.20.0.10",
    state: str = "up",
    hostname: str | None = "web-server",
    ports: str = "",
) -> str:
    hostname_block = (
        f'<hostnames><hostname name="{hostname}" type="PTR"/></hostnames>'
        if hostname
        else "<hostnames/>"
    )
    return f"""<host>
      <status state="{state}" reason="echo-reply"/>
      <address addr="{ip}" addrtype="ipv4"/>
      {hostname_block}
      <ports>{ports}</ports>
    </host>"""


def _make_port(
    portid: int = 80,
    protocol: str = "tcp",
    state: str = "open",
    service_name: str | None = "http",
    product: str | None = "nginx",
    version: str | None = "1.25.0",
    extrainfo: str | None = None,
) -> str:
    attrs = f'name="{service_name}"' if service_name else ""
    if product:
        attrs += f' product="{product}"'
    if version:
        attrs += f' version="{version}"'
    if extrainfo:
        attrs += f' extrainfo="{extrainfo}"'
    return f"""<port protocol="{protocol}" portid="{portid}">
        <state state="{state}" reason="syn-ack"/>
        <service {attrs} method="probed" conf="10"/>
      </port>"""


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestParseNmapXml:

    def test_empty_string_returns_empty_list(self):
        """Empty input → empty list, no exception."""
        result = parse_nmap_xml("")
        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        result = parse_nmap_xml("   \n\t  ")
        assert result == []

    def test_malformed_xml_raises_parse_error(self):
        """Non-XML garbage should raise XmlParseError."""
        with pytest.raises(XmlParseError):
            parse_nmap_xml("this is not xml at all <<<")

    def test_valid_xml_no_hosts(self):
        """Valid nmaprun with zero hosts → empty list."""
        xml = """<?xml version="1.0"?>
        <nmaprun scanner="nmap" version="7.94" xmloutputversion="1.05">
          <runstats><hosts up="0" down="0" total="0"/></runstats>
        </nmaprun>"""
        result = parse_nmap_xml(xml)
        assert result == []

    def test_single_host_single_port(self):
        """One host with one open port — basic happy path."""
        port_xml = _make_port(80, "tcp", "open", "http", "nginx", "1.25.0")
        host_xml = _make_host("172.20.0.10", "up", "web-server", port_xml)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)

        assert len(result) == 1
        host = result[0]
        assert host["ip"] == "172.20.0.10"
        assert host["hostname"] == "web-server"
        assert host["state"] == "up"
        assert len(host["ports"]) == 1

        port = host["ports"][0]
        assert port["port"] == 80
        assert port["protocol"] == "tcp"
        assert port["state"] == "open"
        assert port["name"] == "http"
        assert port["product"] == "nginx"
        assert port["version"] == "1.25.0"

    def test_multiple_hosts(self):
        """Three hosts should all be parsed."""
        h1 = _make_host("172.20.0.10", "up", "web-server",
                         _make_port(80, "tcp", "open", "http", "nginx", "1.25.0"))
        h2 = _make_host("172.20.0.11", "up", "ftp-server",
                         _make_port(21, "tcp", "open", "ftp", "vsftpd", "3.0.5"))
        h3 = _make_host("172.20.0.12", "up", "custom-flask-app",
                         _make_port(5000, "tcp", "open", "http", "Werkzeug", "3.0.4"))
        xml = _make_nmaprun(h1, h2, h3)

        result = parse_nmap_xml(xml)
        assert len(result) == 3

        ips = {h["ip"] for h in result}
        assert ips == {"172.20.0.10", "172.20.0.11", "172.20.0.12"}

    def test_multiple_ports_on_one_host(self):
        """Multiple ports on the same host — all should be extracted."""
        ports = (
            _make_port(80, "tcp", "open", "http", "nginx", "1.25.0")
            + _make_port(443, "tcp", "open", "https", "nginx", "1.25.0")
            + _make_port(22, "tcp", "closed", "ssh")
        )
        host_xml = _make_host("172.20.0.10", "up", "web-server", ports)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert len(result) == 1
        assert len(result[0]["ports"]) == 3

        port_nums = {p["port"] for p in result[0]["ports"]}
        assert port_nums == {80, 443, 22}

    def test_missing_hostname(self):
        """Host with no hostname element — should parse with hostname=None."""
        port_xml = _make_port(80, "tcp", "open", "http")
        host_xml = _make_host("172.20.0.10", "up", None, port_xml)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert len(result) == 1
        assert result[0]["hostname"] is None

    def test_missing_service_version(self):
        """Port with no version info — should parse with version=None."""
        port = """<port protocol="tcp" portid="80">
          <state state="open" reason="syn-ack"/>
          <service name="http" method="table" conf="3"/>
        </port>"""
        host_xml = _make_host("172.20.0.10", "up", "web-server", port)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        port_data = result[0]["ports"][0]
        assert port_data["version"] is None
        assert port_data["product"] is None
        assert port_data["name"] == "http"

    def test_port_no_service_element(self):
        """Port with no <service> element at all — should parse gracefully."""
        port = """<port protocol="tcp" portid="9999">
          <state state="filtered" reason="no-response"/>
        </port>"""
        host_xml = _make_host("172.20.0.10", "up", "web-server", port)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        port_data = result[0]["ports"][0]
        assert port_data["port"] == 9999
        assert port_data["state"] == "filtered"
        assert port_data["name"] is None

    def test_closed_port_included(self):
        """Closed ports should still be included in the result."""
        port_xml = _make_port(22, "tcp", "closed", "ssh")
        host_xml = _make_host("172.20.0.10", "up", "web-server", port_xml)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        port = result[0]["ports"][0]
        assert port["state"] == "closed"

    def test_filtered_port_included(self):
        """Filtered ports should also be included."""
        port_xml = _make_port(8080, "tcp", "filtered")
        host_xml = _make_host("172.20.0.10", "up", "web-server", port_xml)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert result[0]["ports"][0]["state"] == "filtered"

    def test_down_host_is_included(self):
        """Hosts with state=down should still be in the output."""
        host_xml = _make_host("172.20.0.20", "down", None, "")
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert len(result) == 1
        assert result[0]["state"] == "down"
        assert result[0]["ports"] == []

    def test_host_with_no_ports(self):
        """Host with empty <ports/> — services list should be empty."""
        host_xml = _make_host("172.20.0.10", "up", "web-server", "")
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert result[0]["ports"] == []

    def test_extrainfo_captured(self):
        """extrainfo attribute from <service> should be captured."""
        port_xml = _make_port(21, "tcp", "open", "ftp", "vsftpd", "3.0.5", "anonymous")
        host_xml = _make_host("172.20.0.11", "up", "ftp-server", port_xml)
        xml = _make_nmaprun(host_xml)

        result = parse_nmap_xml(xml)
        assert result[0]["ports"][0]["extra_info"] == "anonymous"

    def test_sample_xml_file(self, tmp_path):
        """Parse the project's sample_nmap.xml file."""
        import pathlib
        sample_path = (
            pathlib.Path(__file__).parent.parent.parent
            / "sample-data"
            / "sample_nmap.xml"
        )
        if not sample_path.exists():
            pytest.skip("sample_nmap.xml not found")

        xml_content = sample_path.read_text(encoding="utf-8")
        result = parse_nmap_xml(xml_content)

        # Should parse at least the 3 live hosts
        assert len(result) >= 3

        ips = {h["ip"] for h in result}
        assert "172.20.0.10" in ips
        assert "172.20.0.11" in ips
        assert "172.20.0.12" in ips

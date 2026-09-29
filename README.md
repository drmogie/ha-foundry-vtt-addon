# Tabletop Add-ons

[![Add repository to my Home Assistant][repo-badge]][repo-url]
![Version](https://img.shields.io/badge/version-2026.09.27.03-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Home Assistant add-on repository for running your own tabletop-gaming
stack on Home Assistant.

## Add-ons

- **Foundry VTT** (`foundry_vtt`): runs a Foundry VTT server, using the
  community [felddy/foundryvtt](https://github.com/felddy/foundryvtt-docker)
  container image.
- **DDB Scraper Proxy** (`ddb_scraper_proxy`): fetches a D&D Beyond
  character's public JSON server-side and serves it back with CORS
  headers, so Foundry VTT can pull it directly. Companion to the
  `ddb-live-importer` Foundry module.
- **Foundry VTT MCP & Rest Relay** (`foundry_mcp_rest_relay`): a REST API and
  MCP relay between Foundry VTT and tools like Claude. One login, API tokens,
  a list of recent changes. Pairs with the FGA Relay Connect module and the
  MCP server in [drmogie/foundry-mcp](https://github.com/drmogie/foundry-mcp).
  The image is built by GitHub Actions. After the first build, set the package
  `aarch64-addon-foundry-mcp-rest-relay` and `amd64-addon-foundry-mcp-rest-relay`
  to Public on GitHub.

## Install

1. Click the badge above, or in Home Assistant go to
   Settings, Add-ons, Add-on Store, three-dot menu, Repositories.
2. Add this URL: `https://github.com/drmogie/ha-foundry-vtt-addon`
3. Install **Foundry VTT**, **DDB Scraper Proxy** and/or **Foundry VTT MCP & Rest Relay**.
4. Foundry VTT: fill in your foundryvtt.com login on the Configuration tab,
   start it, and open `http://<your-ha-ip>:30000`.
5. DDB Scraper Proxy: start it as-is (defaults work for public characters).

See [foundry_vtt/DOCS.md](foundry_vtt/DOCS.md) and
[ddb_scraper_proxy/DOCS.md](ddb_scraper_proxy/DOCS.md) for all options. The relay has its own [README](foundry_mcp_rest_relay/README.md).

## You need a Foundry license

Foundry VTT is paid software. This project does not include it. You must own
a license from foundryvtt.com. The container downloads Foundry for you at
first start.

## Credits

- [Foundry Virtual Tabletop](https://foundryvtt.com) by Foundry Gaming LLC.
- [felddy/foundryvtt-docker](https://github.com/felddy/foundryvtt-docker) by
  Mark Feldhousen, MIT license. Foundry VTT add-on is a thin wrapper around it.
- Not affiliated with or endorsed by Foundry Gaming LLC.

[repo-badge]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[repo-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdrmogie%2Fha-foundry-vtt-addon

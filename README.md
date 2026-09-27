# Tabletop Add-ons

[![Add repository to my Home Assistant][repo-badge]][repo-url]
![Version](https://img.shields.io/badge/version-2026.09.26.04-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Home Assistant add-on repository for running your own
[Foundry Virtual Tabletop](https://foundryvtt.com) server on Home Assistant.

## Add-ons

- **Foundry VTT** (`foundry_vtt`): runs a Foundry VTT server, using the
  community [felddy/foundryvtt](https://github.com/felddy/foundryvtt-docker)
  container image.

## Install

1. Click the badge above, or in Home Assistant go to
   Settings, Add-ons, Add-on Store, three-dot menu, Repositories.
2. Add this URL: `https://github.com/drmogie/ha-foundry-vtt-addon`
3. Install **Foundry VTT**.
4. Fill in your foundryvtt.com login on the Configuration tab.
5. Start the add-on and open `http://<your-ha-ip>:30000`.

See [foundry_vtt/DOCS.md](foundry_vtt/DOCS.md) for all options.

## You need a Foundry license

Foundry VTT is paid software. This project does not include it. You must own
a license from foundryvtt.com. The container downloads Foundry for you at
first start.

## Credits

- [Foundry Virtual Tabletop](https://foundryvtt.com) by Foundry Gaming LLC.
- [felddy/foundryvtt-docker](https://github.com/felddy/foundryvtt-docker) by
  Mark Feldhousen, MIT license. This add-on is a thin wrapper around it.
- Not affiliated with or endorsed by Foundry Gaming LLC.

[repo-badge]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[repo-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdrmogie%2Fha-foundry-vtt-addon

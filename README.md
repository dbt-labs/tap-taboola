# tap-taboola

Author: Connor McArthur (connor@fishtownanalytics.com)

### Development

This repository contains two configuration files that need to be copied and filled out before running:

- `config.json.example`: copy to `config.json` in the repo root. Contains:
  - `account_id`, your Taboola account ID (looks like `taboola­demo­advertiser`).
  - `username`, your Taboola username -- used to generate an API access key.
  - `password`, the Taboola password to go along with `username`.
  - `client_id`, your Taboola client ID. You should reach out to your account manager to get this.
  - `client_secret`, your Taboola client secret. You should reach out to your account manager to get this.

- `persist.json.example`: copy to `persist.json` in the repo root. Contains the configuration for the Stitch persister.

Then, the streamer can be run (with persistence) with:

```bash
docker build -f Dockerfile .
docker run <image-id>
```

Or, for interactive development:

```bash
docker build -f Dockerfile .

# this automatically propagates changes into the container
docker -v "$(pwd)":/usr/src/tap-taboola run <image-id>
```

### Gotchas

- `campaigns`: Taboola pushes `null` for `start_date` and `9999-12-31` for `end_date` sometimes. This tap converts `null` dates to `9999-12-31` for consistency. I don't know what that signifies at present. - @cmcarthur=

---

Copyright &copy; 2017 Fishtown Analytics

# tap-taboola

Author: Connor McArthur (connor@fishtownanalytics.com)

This is a [Singer](https://singer.io) tap that produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:
- Pulls raw data from Taboola's Backstage API
- Extracts the following resources:
  - Campaigns
  - Campaign Reports, specifically the `campaign_day_breakdown` report
- Outputs the schema for each resource
- Incrementally pulls data based on the input state


## Quick start

1. Install

    ```bash
    > git clone git@github.com:fishtown-analytics/tap-taboola.git
    > cd tap-taboola
    > pip install .
    ```

2. Get credentials from Taboola:

    You'll need:

    - Your account id (if you aren't sure, contact your account manager)
    - A Taboola username and password with access to the API
    - A client ID and secret for the API (your account manager can give you these)

3. Create the config file.

    There is a template you can use at `config.json.example`, just copy it to `config.json`
    in the repo root and insert your credentials.

    - `account_id`, your Taboola account ID (looks like `taboola­demo­advertiser`).
    - `username`, your Taboola username -- used to generate an API access key.
    - `password`, the Taboola password to go along with `username`.
    - `client_id`, your Taboola client ID. You should reach out to your account manager to get this.
    - `client_secret`, your Taboola client secret. You should reach out to your account manager to get this.
    - `start_date`, the date from which you want to sync data, in the format `2017-03-10`.

4. Run the application.

   ```bash
   tap-taboola --config config.json
   ```

## Gotchas

- `campaigns`: Taboola pushes `null` for `start_date` and `9999-12-31` for `end_date` sometimes. This tap converts `null` dates to `9999-12-31` for consistency. I don't know what that signifies at present. - @cmcarthur=

---

Copyright &copy; 2017 Fishtown Analytics

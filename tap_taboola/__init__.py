#!/usr/bin/env python3

from decimal import Decimal

import argparse
import copy
import datetime
import dateutil.parser
import json
import os
import sys
import time

import requests
import singer
import logging

import tap_taboola.schemas as schemas

logger = singer.get_logger()

BASE_URL = 'https://backstage.taboola.com'

def request(url, access_token, params={}):
    logger.info("Making request: GET {} {}".format(url, params))

    try:
        response = requests.get(
            url,
            headers={'Authorization': 'Bearer {}'.format(access_token),
                     'Accept': 'application/json'},
            params=params)
    except e:
        logger.exception(e)

    logger.info("Got response code: {}".format(response.status_code))

    response.raise_for_status()
    return response


def generate_token(client_id, client_secret, username, password):
    logger.info("Generating new token with password auth")

    url = '{}/backstage/oauth/token'.format(BASE_URL)

    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'username': username,
        'password': password,
        'grant_type': 'password',
    }

    response = requests.post(
        url,
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                 'Accept': 'application/json'},
        params=params)

    logger.info("Got response code: {}".format(response.status_code))

    if response.status_code == 200:
        logger.info("Got an access token.")
    elif response.status_code >= 400 and response.status_code < 500:
        logger.error('{}: {}'.format(response.json().get('error'),
                                     response.json().get('error_description')))
        raise RuntimeError

    return response.json().get('access_token', None)

def parse_campaign_performance(campaign_performance):
    return {
        'campaign_id': int(campaign_performance.get('campaign')),
        'impressions': int(campaign_performance.get('impressions', 0)),
        'ctr': float(campaign_performance.get('ctr', 0.0)),
        'cpc': float(campaign_performance.get('cpc', 0.0)),
        'cpa_actions_num': int(campaign_performance.get('cpa_actions_num', 0)),
        'cpa': float(campaign_performance.get('cpa', 0.0)),
        'cpm': float(campaign_performance.get('cpm', 0.0)),
        'clicks': int(campaign_performance.get('clicks', 0)),
        'currency': str(campaign_performance.get('currency', '')),
        'cpa_conversion_rate': float(campaign_performance.get(
            'cpa_conversion_rate', 0.0)),
        'spent': float(campaign_performance.get('spent', 0.0)),
        'date': str(datetime.datetime.strptime(
            campaign_performance.get('date'),
            '%Y-%m-%d %H:%M:%S.%f'
        ).date()),
    }

def fetch_campaign_performance(config, state, access_token, account_id):
    url = ('{}/backstage/api/1.0/{}/reports/campaign-summary/dimensions/campaign_day_breakdown' # noqa
           .format(BASE_URL, account_id))

    params = {
        'start_date': state.get('start_date', config.get('start_date')),
        'end_date': datetime.date.today(),
    }

    campaign_performance = request(url, access_token, params)
    return campaign_performance.json().get('results')


def sync_campaign_performance(config, state, access_token, account_id):
    performance = fetch_campaign_performance(config, state, access_token,
                                             account_id)

    logger.info("Got {} campaign performance records."
                .format(len(performance)))

    parsed_performance = [parse_campaign_performance(p)
                          for p in performance]

    singer.write_records('campaign_performance', parsed_performance)

    logger.info("Done syncing campaign_performance.")


def parse_campaign(campaign):
    start_date = campaign.get('start_date')
    end_date = campaign.get('end_date')

    return {
        'id': int(campaign.get('id')),
        'advertiser_id': str(campaign.get('advertiser_id', '')),
        'name': str(campaign.get('name', '')),
        'tracking_code': str(campaign.get('tracking_code', '')),
        'cpc': float(campaign.get('cpc', 0.0)),
        'daily_cap': float(campaign.get('daily_cap', 0.0)),
        'spending_limit': float(campaign.get('spending_limit', 0.0)),
        'spending_limit_model': str(campaign.get('spending_limit_model', '')),
        'country_targeting': campaign.get('country_targeting'),
        'platform_targeting': campaign.get('platform_targeting'),
        'publisher_targeting': campaign.get('publisher_targeting'),
        'start_date': str('9999-12-31' if start_date is None else start_date),
        'end_date': str('9999-12-31' if end_date is None else end_date),
        'approval_state': str(campaign.get('approval_state', '')),
        'is_active': bool(campaign.get('is_active', False)),
        'spent': float(campaign.get('spent', 0.0)),
        'status': str(campaign.get('status', '')),
    }

def fetch_campaigns(config, state, access_token, account_id):
    url = '{}/backstage/api/1.0/{}/campaigns/'.format(BASE_URL, account_id)

    response = request(url, access_token)
    return response.json().get('results')


def sync_campaigns(config, state, access_token, account_id):
    campaigns = fetch_campaigns(config, state, access_token, account_id)

    logger.info('Synced {} campaigns.'.format(len(campaigns)))

    parsed_campaigns = [parse_campaign(c) for c in campaigns]

    singer.write_records('campaigns', parsed_campaigns)

    logger.info("Done syncing campaigns.")


def verify_account_access(access_token, account_id):
    url = '{}/backstage/api/1.0/token-details/'.format(BASE_URL)

    result = request(url, access_token)

    if result.json().get('account_id') != account_id:
        logger.error("The provided credentials don't have access to "
                     "`account_id` from the config file.")
        raise RuntimeError
    else:
        logger.info("Verified account access via token details endpoint.")


def validate_config(config):
    required_keys = ['username', 'password', 'account_id',
                     'client_id', 'client_secret', 'start_date']
    missing_keys = []
    null_keys = []
    has_errors = False

    for required_key in required_keys:
        if required_key not in config:
            missing_keys.append(required_key)

        elif config.get(required_key) is None:
            null_keys.append(required_key)

    if len(missing_keys) > 0:
        logger.fatal("Config is missing keys: {}"
                     .format(", ".join(missing_keys)))
        has_errors = True

    if len(null_keys) > 0:
        logger.fatal("Config has null keys: {}"
                     .format(", ".join(null_keys)))
        has_errors = True

    if has_errors:
        raise RuntimeError


def load_config(filename):
    config = {}

    try:
        with open(filename) as f:
            config = json.load(f)
    except:
        logger.fatal("Failed to decode config file. Is it valid json?")
        raise RuntimeError

    validate_config(config)

    return config


def load_state(filename):
    if filename is None:
        return {}

    try:
        with open(filename) as f:
            return json.load(f)
    except:
        logger.fatal("Failed to decode state file. Is it valid json?")
        raise RuntimeError


def do_sync(args):
    logger.info("Starting sync.")

    config = load_config(args.config)
    state = load_state(args.state)

    access_token = generate_token(
        client_id=config.get('client_id'),
        client_secret=config.get('client_secret'),
        username=config.get('username'),
        password=config.get('password'))

    singer.write_schema('campaigns',
                        schemas.campaign,
                        key_properties=['id'])

    singer.write_schema('campaign_performance',
                        schemas.campaign_performance,
                        key_properties=['campaign_id', 'date'])

    verify_account_access(access_token, config.get('account_id'))

    sync_campaigns(config, state, access_token, config.get('account_id'))
    sync_campaign_performance(config, state, access_token,
                              config.get('account_id'))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config', help='Config file', required=True)
    parser.add_argument(
        '-s', '--state', help='State file')

    args = parser.parse_args()

    try:
        do_sync(args)
    except RuntimeError:
        logger.fatal("Run failed.")
        exit(1)



if __name__ == '__main__':
    main()

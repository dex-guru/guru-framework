# https://support.coingecko.com/hc/en-us/articles/32227012396441-Guide-CoinGecko-Supply-Update-Form
import os

import requests
from fastapi import APIRouter

router = APIRouter()

MAX_SUPPLY = 1_000_000_000
TOKEN_DECIMALS = 18
ETHERSCAN_URL = "https://api.etherscan.io/api"
UNCX_ADDRESS = "0xdba68f07d1b7ca219f78ae8582c213d975c25caf"
SABLIER_ADDRESS = "0xafb979d9afad1ad27c5eff4e27226e3ab9e5dcc9"
GNOSIS_SAFE = "0xb77cf7e3cde465d606490145d2aaeef9a9327d29"
QUERY_PARAMS = dict(
    module="account",
    action="tokenbalance",
    contractaddress="0x525574c899a7c877a11865339e57376092168258",
    apikey={os.getenv("ETHERSCAN_API_KEY")},
)


@router.get(
    "/total_supply",
)
async def get_total_supply() -> int:
    return MAX_SUPPLY


@router.get(
    "/circulating_supply",
)
async def get_circulating_supply() -> float:
    res_uncx = requests.get(
        ETHERSCAN_URL, params={**QUERY_PARAMS, "address": UNCX_ADDRESS}
    )
    res_uncx.raise_for_status()
    res_sablier = requests.get(
        ETHERSCAN_URL, params={**QUERY_PARAMS, "address": SABLIER_ADDRESS}
    )
    res_sablier.raise_for_status()
    res_safe = requests.get(
        ETHERSCAN_URL, params={**QUERY_PARAMS, "address": GNOSIS_SAFE}
    )
    res_safe.raise_for_status()
    return MAX_SUPPLY - (
        (
            int(res_uncx.json()["result"])
            + int(res_sablier.json()["result"])
            + int(res_safe.json()["result"])
        )
        / 10**TOKEN_DECIMALS
    )

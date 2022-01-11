"""
load transactions periodically, store to file, update with new ones
"""
import time
import spl.token.instructions
from solana.publickey import PublicKey
from solana.rpc.api import Client, Keypair
from utils import is_nft_purchase, treasury_address
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
import base58
from config import private_key, available_nfts_initial
import pickle

# consts
processed_tx_sigs_fpath = './processed_tx_sigs.p'
available_nfts_fpath = './available_nfts.p'
delay_period_seconds = 30

# first time setup
try:
    available_nfts = pickle.load(open(available_nfts_fpath, 'rb'))
except FileNotFoundError as e:
    pickle.dump(available_nfts_initial, open(available_nfts_fpath, 'wb'))

# setup
solana_client = Client("https://api.mainnet-beta.solana.com/")
byte_array = base58.b58decode(private_key)
keypair = Keypair.from_secret_key(byte_array)
processed_tx_sigs = pickle.load(open(processed_tx_sigs_fpath, 'rb'))
available_nfts = pickle.load(open(available_nfts_fpath, 'rb'))

while True:
    # run this periodically, maintain a local hashmap/dict of tx_sigs to makesure we don't process same twice
    # note: can optimize this by setting the 'to=' field of get_signatures_for_address() to most recently processed sig
    tx_sigs = [d['signature'] for d in solana_client.get_signatures_for_address(PublicKey(treasury_address), limit=1000)['result']]
    for sig in tx_sigs:
        if sig in processed_tx_sigs:
            continue
        tx = solana_client.get_transaction(sig)
        buyer_address = is_nft_purchase(tx)
        if buyer_address:
            # send nft
            nft_mint = PublicKey(available_nfts[0][0])
            nft_token_account = PublicKey(available_nfts[0][1])
            token = Token(solana_client, nft_mint, TOKEN_PROGRAM_ID, keypair)
            # lookup ata for receiver
            ata = spl.token.instructions.get_associated_token_address(PublicKey(buyer_address), nft_mint)
            # create ata
            try:
                token.get_account_info(ata)
                res = token.transfer(nft_token_account, PublicKey(ata), keypair, 1)
                del available_nfts[0]
                pickle.dump(available_nfts, open(available_nfts_fpath, 'wb'))
                print(f"tx to {ata} for user {buyer_address} with res {res}")
            except Exception as e:
                ata = token.create_associated_token_account(PublicKey(buyer_address))
                time.sleep(5)
                continue # don't want to mark this as processed... just skip it for now and comback next time
        # update processed sigs
        processed_tx_sigs.add(sig)
        pickle.dump(processed_tx_sigs, open(processed_tx_sigs_fpath, 'wb'))
    # sleep to avoid rpc throttling
    time.sleep(delay_period_seconds)





## config and helpers
from config import nft_price_lamports, treasury_address
system_program_address = '11111111111111111111111111111111'

# test code
# test_sig = 'Gfg5BA8WFqxc7UG5AHqGuA8NQeqPHzPtfUa9wELhKTzxA9tjQKQ1cAdcjZRoNKcpb9JA5C9j61btCu5TGA8rfhj'
# test_tx = solana_client.get_transaction(test_sig)


def is_nft_purchase(tx):
    # return None or address of nft buyer
    msg = tx['result']['transaction']['message']
    ixs = msg['instructions']
    # should only have one instruction in the transaction
    if len(ixs) != 1:
        return None
    # should only have three account keys, from addy, to addy, and system program
    if len(msg['accountKeys']) != 3:
        return None
    prog_idx = ixs[0]['programIdIndex']
    program_address = msg['accountKeys'][prog_idx]
    # should be a system program transfer
    if program_address != system_program_address:
        return None
    from_addy = msg['accountKeys'][0]
    to_addy = msg['accountKeys'][1]
    # transfer must be to our treasury
    if to_addy != treasury_address:
        return None
    pre_balances = tx['result']['meta']['preBalances']
    post_balances = tx['result']['meta']['postBalances']
    treasury_balance_delta = post_balances[1] - pre_balances[1]
    if treasury_balance_delta >= nft_price_lamports:
        return from_addy
    else:
        return None

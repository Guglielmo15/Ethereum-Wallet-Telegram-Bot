import random
import string
import time
import telebot
import web3
import secrets
from eth_account import Account

bot = telebot.TeleBot("INSERT YOUR BOT TOKEN")

# Dictionary to store user wallet information (Replace with secure storage in production)
user_wallets = []


def create_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    public_key = Account.from_key(private_key)
    user_wallets.append(private_key)
    return private_key, public_key


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.send_message(message.chat.id, """Welcome to the Ethereum wallet bot! \U0001F916

I can help you create a wallet and send and receive ETH. Here are the commands you can use:

/help - Show all the commands
/createWallet - Create a new wallet                                            
/importWallet - Import your existing wallet using the private key
/balance - Show your ETH balance
/send - Send ETH or any other token

Enjoy! \U0001F680""")


@bot.message_handler(commands=["createWallet"])
def create_wallet_handler(message):
    private_key, public_key = create_wallet()
    bot.send_message(message.chat.id, "Your wallet has been created! Here are your keys:")
    bot.send_message(message.chat.id, "Private key: {}".format(private_key))
    bot.send_message(message.chat.id, "Public key: {}".format(public_key.address))


@bot.message_handler(commands=["importWallet"])
def import_wallet_command(message):
    bot.send_message(message.chat.id, "Please enter your private key:")
    bot.register_next_step_handler(message, process_private_key)


def process_private_key(message):
    private_key = message.text.strip()
    if is_valid_private_key(private_key):
        user_wallets.append(private_key)
        public_key = Account.from_key(private_key)
        bot.send_message(message.chat.id, f"Congrats! Your wallet has been imported.\n\nHere is your public key: {public_key.address}")
    else:
        bot.send_message(message.chat.id, "Invalid private key. Please enter a valid private key in hex format starting with '0x'.")
        bot.register_next_step_handler(message, process_private_key)


def is_valid_private_key(private_key):
    try:
        test = Account.from_key(private_key)
        return True
    except Exception:
        return False


@bot.message_handler(commands=["balance"])
def balance_command(message):
    if len(user_wallets) > 0:
        w3 = web3.Web3(web3.Web3.HTTPProvider('INSERT YOUR BLOCKCHAIN ENDPOINT HERE'))

        private_key = user_wallets[0]
        public_key = Account.from_key(private_key)
        balance_wei = w3.eth.get_balance(public_key.address)
        balance_eth = balance_wei / 1e18
        formatted_balance = "{:.4f}".format(balance_eth)
        bot.send_message(message.chat.id, f"Your ETH balance: {formatted_balance} ETH")
    else:
        bot.send_message(message.chat.id, "You need to create or import a wallet first. Use /createWallet or /importWallet to create or import a wallet.")


@bot.message_handler(commands=["send"])
def send_command(message):
    if len(user_wallets) > 0:
        bot.send_message(message.chat.id, "Please enter the amount you want to send:")
        bot.register_next_step_handler(message, process_amount)
    else:
        bot.send_message(message.chat.id, "You need to create or import a wallet first. Use /createWallet or /importWallet to create or import a wallet.")


def process_amount(message):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
        bot.send_message(message.chat.id, "Please enter the receiver's address:")
        bot.register_next_step_handler(message, process_receiver_address, amount)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid amount. Please enter a valid number greater than 0.")
        bot.register_next_step_handler(message, process_amount)


def process_receiver_address(message, amount):
    receiver_address = message.text.strip()
    if not is_valid_address(receiver_address):
        bot.send_message(message.chat.id, "Invalid receiver address. Please enter a valid Ethereum address.")
        bot.register_next_step_handler(message, process_receiver_address, amount)
    else:
        # Perform the transaction logic here (send amount from user's wallet to receiver_address)
        private_key = user_wallets[0]
        try:
            tx_hash = send_transaction(private_key, receiver_address, amount)
            bot.send_message(message.chat.id, f"Transaction sent successfully! Transaction Hash: {tx_hash.hex()}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Error occurred while sending transaction: {str(e)}")


def is_valid_address(address):
    try:
        web3.Web3.is_address(address)
        return True
    except web3.exceptions.InvalidAddress:
        return False

def send_transaction(private_key, receiver_address, amount):
    w3 = web3.Web3(web3.Web3.HTTPProvider('INSERT YOUR BLOCKCHAIN ENDPOINT HERE'))
    account = Account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    gas_limit = 21000  # Default gas limit for a simple transfer
    value = w3.to_wei(amount, 'ether')
    transaction = {
        'nonce': nonce,
        'to': receiver_address,
        'value': value,
        'gasPrice': gas_price,
        'gas': gas_limit
    }
    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    return tx_hash


if __name__ == "__main__":
    print("Ok \U0001F680")
    bot.polling()

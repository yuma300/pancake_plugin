import uuid
from decimal import Decimal

from senkalib.caaj_journal import CaajJournal
from senkalib.caaj_plugin import CaajPlugin
from senkalib.chain.bsc.bsc_transaction import BscTransaction
from senkalib.token_original_id_table import TokenOriginalIdTable

# PancakeSwap: Router v2
PANCAKESWAP_ADDRESS_TRADE = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

PANCAKESWAP_ADDRESS_EARN = "0x73feaa1eE314F8c655E354234017bE2193C9E24E"
PANCAKESWAP_SYRUP_ADDRESS = "0x009cf7bc57584b7998236eff51b98a168dcea9b0"

CAKE_CONTRACT_ADDRESS = "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
WBNB_CONTRACT_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
SYRUP_CONTRACT_ADDRESS = "0x009cF7bC57584b7998236eff51b98A168DceA9B0"

PANCAKESWAP_ADDRESS = [
    PANCAKESWAP_ADDRESS_EARN,
    PANCAKESWAP_ADDRESS_TRADE,
    CAKE_CONTRACT_ADDRESS,
]

LP_DEPOSIT_TOPIC = "0x90890809c654f11d6e72a28fa60149770a0d11ec6c92319d6ceb2bb0a4ea1a15"
LP_WITHDROW_TOPIC = "0xf279e6a1f5e320cca91135676d9cb6e44ca8a08c0b88342bcdb1144f6511b568"


WETH_CONTRACT_ADDRESS = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
WETH_DEPOSIT_TOPIC = (
    "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
)
WETH_WITHDRAWAL_TOPIC = (
    "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65"
)

WETH_EARN_WITHDRAWAL_TOPIC = (
    "0xf279e6a1f5e320cca91135676d9cb6e44ca8a08c0b88342bcdb1144f6511b568"
)


ERC20_TRANSFER_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)
ERC20_APPROVE_TOPIC = (
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
)
ERC20_BURN_TOPIC = "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496"
ERC20_MINT_TOPIC = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"

WEI = 10**18


class PancakePlugin(CaajPlugin):
    CHAIN = "bsc"
    PLATFORM = "pancakeswap"

    @classmethod
    def can_handle(cls, transaction) -> bool:
        swap_type = transaction.transaction_receipt["to"]
        if swap_type in PANCAKESWAP_ADDRESS:
            return True
        else:
            return False

    @classmethod
    def get_caajs(
        cls,
        address: str,
        transaction: BscTransaction,
        token_table: TokenOriginalIdTable,
    ) -> list:
        caajs = []
        trade_uuid = cls._get_uuid()
        topics = list(
            map(
                lambda log: log["topics"][0].hex().lower(),
                transaction.transaction_receipt["logs"],
            )
        )
        if transaction.transaction_receipt["status"] == 1:
            if transaction.transaction_receipt["to"] == PANCAKESWAP_ADDRESS_TRADE:

                if ERC20_BURN_TOPIC in topics:
                    # TODO: liquidity remove
                    # caaj_main = cls__get_caaj_liquidity_remove(
                    #     transaction, topics
                    # )
                    caaj_fee = cls.__get_caaj_fee(
                        transaction, "pancakeswap transaction fee", trade_uuid
                    )
                    caajs.append(caaj_fee)
                elif ERC20_MINT_TOPIC in topics:
                    # TODO: liquidity add
                    # caaj_main = cls__get_caaj_liquidity_add(
                    #     transaction, topics
                    # )
                    caaj_fee = cls.__get_caaj_fee(
                        transaction, "pancakeswap transaction fee", trade_uuid
                    )
                    caajs.append(caaj_fee)

                else:
                    # exchange
                    caajs = cls.__get_caaj_exchange(
                        transaction, topics, trade_uuid, token_table
                    )
                    caaj_fee = cls.__get_caaj_fee(
                        transaction, "pancakeswap transaction fee", trade_uuid
                    )
                    caajs.append(caaj_fee)

            elif transaction.transaction_receipt["to"] == PANCAKESWAP_ADDRESS_EARN:
                if WETH_EARN_WITHDRAWAL_TOPIC in topics:
                    # TODO: unstake
                    # caaj_main = cls.__get_caaj_farms_unstake(transaction)
                    caaj_fee = cls.__get_caaj_fee(
                        transaction, "pancakeswap transaction fee", trade_uuid
                    )
                    caajs.append(caaj_fee)
                    # caaj_reward = cls.__get_caaj_farms_reward(transaction)

                else:
                    # TODO: stake and harvest
                    # caaj_main = cls.__get_caaj_farms_stake(transaction)
                    caaj_fee = cls.__get_caaj_fee(
                        transaction, "pancakeswap transaction fee", trade_uuid
                    )
                    caajs.append(caaj_fee)
        return caajs

    @classmethod
    def __get_caaj_fee(cls, transaction: BscTransaction, comment: str, trade_uuid: str):
        return CaajJournal(
            transaction.get_timestamp(),
            cls.CHAIN,
            cls.PLATFORM,
            cls.CHAIN,
            transaction.get_transaction_id(),
            trade_uuid,
            "lose",
            str(Decimal(transaction.get_transaction_fee()) / Decimal(WEI)),
            "bnb",
            "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
            "87dae675-c183-c452-fffa-ac519b71df01",
            transaction.transaction_receipt["from"],
            "0x0000000000000000000000000000000000000000",
            comment,
        )

    @classmethod
    def __get_caaj_exchange(
        cls,
        transaction: BscTransaction,
        topics: list[str],
        trade_uuid: str,
        token_table: TokenOriginalIdTable,
    ) -> list[CaajJournal]:
        caajs = []
        caaj_common = cls.__get_caaj_common(transaction)
        if WETH_DEPOSIT_TOPIC in topics:
            credit_log_index = topics.index(WETH_DEPOSIT_TOPIC)

            token_original_id = WBNB_CONTRACT_ADDRESS
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)

            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "lose",
                    str(
                        Decimal(
                            int(
                                transaction.transaction_receipt["logs"][
                                    credit_log_index
                                ]["data"],
                                16,
                            )
                        )
                        / Decimal(WEI)
                    ),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["credit_from"],
                    caaj_common["credit_to"],
                    "pancakeswap swap",
                )
            )

            debit_log = list(
                filter(
                    lambda log: "0x" + log["topics"][2].hex().lower()[26:]
                    == transaction.transaction_receipt["from"].lower(),
                    cls.__get_transfer_logs_from_transaction(transaction),
                )
            )[-1]

            token_original_id = debit_log["address"]
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)
            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "get",
                    str(Decimal(int(debit_log["data"], 16)) / Decimal(WEI)),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["debit_from"],
                    caaj_common["debit_to"],
                    "pancakeswap swap",
                )
            )

        elif WETH_WITHDRAWAL_TOPIC in topics:
            debit_log_index = topics.index(WETH_WITHDRAWAL_TOPIC)
            credit_log = list(
                filter(
                    lambda log: "0x" + log["topics"][1].hex().lower()[26:]
                    == transaction.transaction_receipt["from"].lower(),
                    cls.__get_transfer_logs_from_transaction(transaction),
                )
            )[0]

            token_original_id = credit_log["address"]
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)
            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "lose",
                    str(Decimal(int(credit_log["data"], 16)) / Decimal(WEI)),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["credit_from"],
                    caaj_common["credit_to"],
                    "pancakeswap swap",
                )
            )

            token_original_id = WBNB_CONTRACT_ADDRESS
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)

            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "get",
                    str(
                        Decimal(
                            int(
                                transaction.transaction_receipt["logs"][
                                    debit_log_index
                                ]["data"],
                                16,
                            )
                        )
                        / Decimal(WEI)
                    ),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["debit_from"],
                    caaj_common["debit_to"],
                    "pancakeswap swap",
                )
            )

        else:
            credit_log = list(
                filter(
                    lambda log: f"0x{log['topics'][1].hex().lower()[26:]}"
                    == transaction.transaction_receipt["from"].lower(),
                    cls.__get_transfer_logs_from_transaction(transaction),
                )
            )[0]
            token_original_id = credit_log["address"]
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)
            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "lose",
                    str(Decimal(int(credit_log["data"], 16)) / Decimal(WEI)),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["credit_from"],
                    caaj_common["credit_to"],
                    "pancakeswap swap",
                )
            )
            debit_log = list(
                filter(
                    lambda log: f"0x{log['topics'][2].hex().lower()[26:]}"
                    == transaction.transaction_receipt["from"].lower(),
                    cls.__get_transfer_logs_from_transaction(transaction),
                )
            )[-1]
            token_original_id = debit_log["address"]
            token_symbol = token_table.get_symbol(cls.CHAIN, token_original_id)
            symbol_uuid = token_table.get_symbol_uuid(cls.CHAIN, token_original_id)
            caajs.append(
                CaajJournal(
                    transaction.get_timestamp(),
                    cls.CHAIN,
                    cls.PLATFORM,
                    cls.CHAIN,
                    transaction.get_transaction_id(),
                    trade_uuid,
                    "get",
                    str(Decimal(int(debit_log["data"], 16)) / Decimal(WEI)),
                    token_symbol,
                    token_original_id,
                    symbol_uuid,
                    caaj_common["debit_from"],
                    caaj_common["debit_to"],
                    "pancakeswap swap",
                )
            )

        return caajs

    # TODO: liquidity系が利用できるようになったら実装
    # @classmethod
    # def __get_caaj_liquidity_add(cls, transaction, topics):
    #     caaj_common = cls.__get_caaj_common(transaction)

    #     if WETH_DEPOSIT_TOPIC in topics:
    #         # incluede bnb
    #         credit_log_index_1 = topics.index(WETH_DEPOSIT_TOPIC)
    #         credit_log_2 = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][1].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[0]
    #         debit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][2].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[-1]
    #         caaj_main = {
    #             "debit_title": "LIQUIDITY",
    #             "debit_amount": {
    #                 debit_log["address"].lower(): str(
    #                     Decimal(int(debit_log["data"].lower(), 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "credit_title": "SPOT",
    #             "credit_amount": {
    #                 cls.CHAIN_CONTRACT: str(
    #                     Decimal(
    #                         int(
    #                             transaction.transaction_receipt["logs"][
    #                                 credit_log_index_1
    #                             ]["data"].lower(),
    #                             16,
    #                         )
    #                     )
    #                     / Decimal(WEI)
    #                 ),
    #                 credit_log_2["address"].lower(): str(
    #                     Decimal(int(credit_log_2["data"].lower(), 16)) / Decimal(WEI)
    #                 ),
    #             },
    #             "comment": "pancakeswap add liquidity",
    #         }
    #         caaj_main.update(caaj_common)
    #         return caaj_main

    #     else:
    #         credit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][1].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )
    #         debit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][2].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[-1]
    #         caaj_main = {
    #             "debit_title": "LIQUIDITY",
    #             "debit_amount": {
    #                 debit_log["address"]: str(
    #                     Decimal(int(debit_log["data"], 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "credit_title": "SPOT",
    #             "credit_amount": {
    #                 credit_log[0]["address"]: str(
    #                     Decimal(int(credit_log[0]["data"], 16)) / Decimal(WEI)
    #                 ),
    #                 credit_log[1]["address"]: str(
    #                     Decimal(int(credit_log[1]["data"], 16)) / Decimal(WEI)
    #                 ),
    #             },
    #             "comment": "pancakeswap add liquidity",
    #         }
    #         caaj_main.update(caaj_common)
    #         return caaj_main

    # @classmethod
    # def __get_caaj_liquidity_remove(cls, transaction, topics):
    #     caaj_common = cls.__get_caaj_common(transaction)
    #     if WETH_WITHDRAWAL_TOPIC in topics:
    #         debit_log_1_index = topics.index(WETH_WITHDRAWAL_TOPIC)
    #         debit_log_2 = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][2].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[-1]

    #         credit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][1].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[0]
    #         caaj_main = {
    #             "debit_title": "SPOT",
    #             "debit_amount": {
    #                 debit_log_2["address"]: str(
    #                     Decimal(int(debit_log_2["data"], 16)) / Decimal(WEI)
    #                 ),
    #                 cls.CHAIN_CONTRACT: str(
    #                     Decimal(
    #                         int(
    #                             transaction.transaction_receipt["logs"][
    #                                 debit_log_1_index
    #                             ]["data"],
    #                             16,
    #                         )
    #                     )
    #                     / Decimal(WEI)
    #                 ),
    #             },
    #             "credit_title": "LIQUIDITY",
    #             "credit_amount": {
    #                 credit_log["address"]: str(
    #                     Decimal(int(credit_log["data"], 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "comment": "pancakeswap remove liquidity",
    #         }
    #         caaj_main.update(caaj_common)
    #         return caaj_main
    #     else:
    #         debit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][2].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )
    #         credit_log = list(
    #             filter(
    #                 lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #                 and "0x" + log["topics"][1].hex().lower()[26:]
    #                 == transaction.transaction_receipt["from"].lower(),
    #                 transaction.transaction_receipt["logs"],
    #             )
    #         )[0]
    #         caaj_main = {
    #             "debit_title": "SPOT",
    #             "debit_amount": {
    #                 debit_log[0]["address"]: str(
    #                     Decimal(int(debit_log[0]["data"], 16)) / Decimal(WEI)
    #                 ),
    #                 debit_log[1]["address"]: str(
    #                     Decimal(int(debit_log[1]["data"], 16)) / Decimal(WEI)
    #                 ),
    #             },
    #             "credit_title": "LIQUIDITY",
    #             "credit_amount": {
    #                 credit_log["address"]: str(
    #                     Decimal(int(credit_log["data"], 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "comment": "pancakeswap remove liquidity",
    #         }
    #         caaj_main.update(caaj_common)
    #         return caaj_main

    @classmethod
    def __get_caaj_common(cls, transaction):
        caaj_common = {
            "transaction_id": transaction.transaction_receipt["transactionHash"],
            "debit_from": transaction.transaction_receipt["to"],
            "debit_to": transaction.transaction_receipt["from"],
            "credit_from": transaction.transaction_receipt["from"],
            "credit_to": transaction.transaction_receipt["to"],
        }
        return caaj_common

    @classmethod
    def __get_transfer_logs_from_transaction(cls, transaction: BscTransaction) -> list:
        return list(
            filter(
                lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC,
                transaction.transaction_receipt["logs"],
            )
        )

    # TODO: liquidity系が利用できるようになったら実装
    # @classmethod
    # def __get_caaj_farms_unstake(cls, transaction):
    #     caaj_common = cls.__get_caaj_common(transaction)

    #     debit_log = list(
    #         filter(
    #             lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #             and "0x" + log["topics"][2].hex().lower()[26:]
    #             == transaction.transaction_receipt["from"].lower()
    #             and "0x" + log["topics"][1].hex().lower()[26:]
    #             == transaction.transaction_receipt["to"].lower(),
    #             transaction.transaction_receipt["logs"],
    #         )
    #     )[0]
    #     caaj_main = {
    #         "debit_title": "LIQUIDITY",
    #         "debit_amount": {
    #             debit_log["address"]: str(
    #                 Decimal(int(debit_log["data"], 16)) / Decimal(WEI)
    #             )
    #         },
    #         "credit_title": "UNSTAKE",
    #         "credit_amount": {
    #             debit_log["address"]: str(
    #                 Decimal(int(debit_log["data"], 16)) / Decimal(WEI)
    #             )
    #         },
    #         "comment": "pancakeswap reward",
    #     }
    #     caaj_main.update(caaj_common)
    #     return caaj_main

    # @classmethod
    # def __get_caaj_farms_reward(cls, transaction):
    #     debit_log_reward = list(
    #         filter(
    #             lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #             and "0x" + log["topics"][2].hex().lower()[26:]
    #             == transaction.transaction_receipt["from"].lower()
    #             and "0x" + log["topics"][1].hex().lower()[26:]
    #             == SYRUP_CONTRACT_ADDRESS.lower(),
    #             transaction.transaction_receipt["logs"],
    #         )
    #     )[0]

    #     caaj_reward = {
    #         "time": transaction.get_timestamp(),
    #         "platform": cls.PLATFORM,
    #         "transaction_id": transaction.transaction_receipt["transactionHash"],
    #         "debit_title": "SPOT",
    #         "debit_from": SYRUP_CONTRACT_ADDRESS,
    #         "debit_to": transaction.transaction_receipt["from"],
    #         "debit_amount": {
    #             debit_log_reward["address"]: str(
    #                 Decimal(int(debit_log_reward["data"], 16)) / Decimal(WEI)
    #             )
    #         },
    #         "credit_title": "STAKINGREWARD",
    #         "credit_amount": {
    #             debit_log_reward["address"]: str(
    #                 Decimal(int(debit_log_reward["data"], 16)) / Decimal(WEI)
    #             )
    #         },
    #         "credit_from": transaction.transaction_receipt["from"],
    #         "credit_to": SYRUP_CONTRACT_ADDRESS,
    #         "comment": "pancakeswap reward",
    #     }
    #     return caaj_reward

    # @classmethod
    # def __get_caaj_farms_stake(cls, transaction):
    #     caaj_common = cls.__get_caaj_common(transaction)

    #     debit_log = list(
    #         filter(
    #             lambda log: log["topics"][0].hex().lower() == ERC20_TRANSFER_TOPIC
    #             and "0x" + log["topics"][1].hex().lower()[26:]
    #             == transaction.transaction_receipt["from"].lower()
    #             and "0x" + log["topics"][2].hex().lower()[26:]
    #             == transaction.transaction_receipt["to"].lower(),
    #             transaction.transaction_receipt["logs"],
    #         )
    #     )
    #     if len(debit_log) == 0:
    #         # harvest
    #         caaj_harvest = cls.__get_caaj_farms_reward(transaction)
    #         return caaj_harvest
    #     else:
    #         # stake
    #         caaj_main = {
    #             "debit_title": "STAKING",
    #             "debit_amount": {
    #                 debit_log[0]["address"]: str(
    #                     Decimal(int(debit_log[0]["data"], 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "credit_title": "LIQUIDITY",
    #             "credit_amount": {
    #                 debit_log[0]["address"]: str(
    #                     Decimal(int(debit_log[0]["data"], 16)) / Decimal(WEI)
    #                 )
    #             },
    #             "comment": "pancakeswap stake",
    #         }
    #         caaj_main.update(caaj_common)
    #         return caaj_main

    @classmethod
    def _get_uuid(cls) -> str:
        return str(uuid.uuid4())

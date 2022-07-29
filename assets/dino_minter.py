from pyteal import *
from pyteal.ast.bytes import Bytes

def approval():
    MAX_UNITS = Int(1000)

    # locals
    whitelisted = Bytes("whitelisted")
    unclaimed_asset = Bytes("unclaimed")
    last_tier_minted = Bytes("last_tier_minted")
    user_minted_current_tier = Bytes("user_minted_current_tier")
    # globals
    minted_units = Bytes("minted_units")
    manager = Bytes("manager")
    whitelist_count = Bytes("whitelist_count")
    current_tier  = Bytes("current_tier")
    minted_current_tier = Bytes("minted_current_tier")
    price = Bytes("price")
    is_open = Bytes("is_open")
    tier_limit = Bytes("tier_limit")
    tier_limit_per_user = Bytes("tier_limit_per_user")
    # Operations
    set_manager = Bytes("set_manager")
    buy = Bytes("buy")
    claim = Bytes("claim")
    set_whitelist= Bytes("set_whitelist")
    redeem = Bytes("redeem")
    increase_tier = Bytes("increase_tier")
    open_minting = Bytes("open")
    #Scratch
    s = ScratchVar(TealType.uint64)
    asset = ScratchVar(TealType.uint64)


#
#
#    SUBROUTINES
#
#


# 
# Computes discount for user based on whitelist status
# Args: account (str): the requesting user Algorand address
#
    @Subroutine(TealType.uint64)
    def compute_total_price(account):
        account_tier_status = App.localGet(account, whitelisted)
        discount = Div(App.globalGet(price), Int(10))
        return (
            If(account_tier_status > Int(0))
            .Then(Minus(App.globalGet(price), discount))
            .Else(App.globalGet(price))
        )
#
# To be called after minting, increases minted unit counters
# Args: sender (str): the requesting user Algorand address
#
    @Subroutine(TealType.none)
    def increase_minted_units(sender):
        incr_mint = App.globalGet(minted_units) + Int(1)
        incr_current_tier_mint = App.globalGet(minted_current_tier) + Int(1)
        incr_user_minted_current_tier = App.localGet(sender, user_minted_current_tier) + Int(1)
        return Seq(
            App.globalPut(minted_units, incr_mint),
            App.globalPut(minted_current_tier, incr_current_tier_mint),
            App.globalPut(user_minted_current_tier, incr_user_minted_current_tier)
        )

#
# Handles internal minting Tx
# Args: 
#       url: NFT target URL
#       metadata: NFT metadata    @Subroutine(TealType.none)
    def execute_mint_tx(url, metadata):
         return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_total: Int(1),
                TxnField.config_asset_decimals: Int(0),
                TxnField.config_asset_unit_name: Bytes("DYN"),
                TxnField.config_asset_name: Bytes("Dyno"),
                TxnField.config_asset_default_frozen: Int(0),
                TxnField.config_asset_clawback: Global.current_application_address(),
                TxnField.config_asset_manager: App.globalGet(manager),
                TxnField.config_asset_url: url,
                TxnField.note: metadata,
                TxnField.fee: Global.min_txn_fee()
            }),
            InnerTxnBuilder.Submit(),
            asset.store(InnerTxn.created_asset_id())
            
        ])
#
# Handles Asset transfer to buyer
# Args: asset_id: unique ASA Id to be transferred
#
    @Subroutine(TealType.none)
    def transfer_asset(asset_id):
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder().SetFields({
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: asset_id,
                TxnField.asset_amount: Int(1),
                TxnField.asset_sender: Global.current_application_address(),
                TxnField.asset_receiver: Txn.sender()
            }),
            InnerTxnBuilder.Submit()
        ])

#
# Handles payments to be sent from the App
# Args:
#       receiver: recipient of payment. User in case of change being sent back, manager in case of fund redemption
#       amount: amount to be sent in microAlgos
#
    @Subroutine(TealType.none)
    def send_payment(receiver, amount):
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: amount,
                TxnField.sender: Global.current_application_address(),
                TxnField.receiver: receiver,
                TxnField.fee: Global.min_txn_fee()
            }),
            InnerTxnBuilder.Submit(),
        ])        

    



    basic_checks = And(
        Txn.rekey_to() == Global.zero_address(),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.asset_close_to() == Global.zero_address(),
    )
    
    on_deploy = Seq([
        Assert(
            And(
                Global.group_size() == Int(1),
                basic_checks
            )
        ),
        App.globalPut(whitelist_count, Int(0)),
        App.globalPut(manager, Txn.sender()),
        App.globalPut(minted_units, Int(0)),
        App.globalPut(current_tier, Int(0)),
        Approve()
    ])

    handle_optin = Seq([
        Assert(And(
            Global.group_size() == Int(1),
            Txn.application_args.length() == Int(0),
            basic_checks
        )),
        App.localPut(Txn.sender(), whitelisted, Int(0)),
        App.localPut(Txn.sender(), unclaimed_asset, Int(0)),
        Approve(),
        
    ])

    handle_payment = Seq(
        Assert( Global.group_size() == Int(2)),
        s.store(compute_total_price(Gtxn[1].sender())),
        Assert(And(        
            Gtxn[1].type_enum() == TxnType().Payment,
            Gtxn[0].sender() == App.globalGet(manager),
            Gtxn[1].amount() >= s.load(),
            Gtxn[1].receiver() == Global.current_application_address(),
            App.localGet(Gtxn[1].sender(), unclaimed_asset) == Int(0),
            ),
        ),
        If(App.localGet(Gtxn[1].sender(), last_tier_minted) < App.globalGet(current_tier))
        .Then(
            Seq(
                App.localPut(Gtxn[1].sender(), last_tier_minted, App.globalGet(current_tier)),
                App.localPut(Gtxn[1].sender(), user_minted_current_tier, Int(0))
            )
        ),
        Assert(
            And(
                App.globalGet(minted_units) <= MAX_UNITS,
                App.globalGet(minted_current_tier) <= App.globalGet(tier_limit),
                App.localGet(Gtxn[1].sender(), user_minted_current_tier) <= App.globalGet(tier_limit_per_user)
        )),
        If(
            App.globalGet(is_open) == Int(0),
            Assert(
            App.localGet(Gtxn[1].sender(), whitelisted) == App.globalGet(current_tier))
            ),
        execute_mint_tx(Gtxn[0].application_args[1], Gtxn[0].application_args[2]),
        App.localPut(Gtxn[1].sender(), unclaimed_asset, asset.load()),
        increase_minted_units(Gtxn[1].sender()),
        If(
            Gtxn[1].amount() > (s.load() + Global.min_txn_fee()),
            send_payment(Gtxn[1].sender(), (Gtxn[1].amount() - s.load() - Global.min_txn_fee()))
        ),

        Approve()
    )

    handle_claim = Seq(
        Assert(
            Txn.assets[0] == App.localGet(Txn.sender(), unclaimed_asset)
        ),
        transfer_asset(App.localGet(Txn.sender(), unclaimed_asset)),
        App.localPut(Txn.sender(), unclaimed_asset, Int(0)),
        Approve()
        )
    

    add_whitelist = Seq([
            Assert(And(
                Global.group_size() == Int(1),
                Txn.accounts.length() == Int(1),
                Txn.application_args.length() == Int(2),
                basic_checks,
                Txn.sender() == App.globalGet(manager),
            )),
            If(
                App.localGet(Txn.accounts[1], whitelisted) == Int(0),
                App.globalPut(whitelist_count, App.globalGet(whitelist_count) + Int(1)),
            ),
            App.localPut(Txn.accounts[1], whitelisted, Btoi(Txn.application_args[1])),
            Approve()
        ])

    handle_delete = Seq(
        Assert(
            And(
                Txn.sender() == App.globalGet(manager),
                Global.group_size() == Int(1)
            )
        ),
        Approve()
    )

    handle_update = Seq(
        Assert(
            And(Txn.sender() == App.globalGet(manager),
            Global.group_size() == Int(1)
            )
        ),
        Approve()
    )

    handle_redeem = Seq(
        Assert(
            And(
            Txn.sender() == App.globalGet(manager),
            Global.group_size() == Int(1))
            ),
        send_payment(Txn.sender(), Txn.application_args[1]),
        Approve()
    )

    handle_set_manager = Seq([
            Assert(
                And(
                    Global.group_size() == Int(1),
                    Txn.accounts.length() == Int(1),
                    basic_checks,
                    Txn.sender() == App.globalGet(manager),
                )
            ),
            App.globalPut(manager, Txn.accounts[1]),
            Approve()
        ])

    handle_increase_tier = Seq([
        Assert(
            And(
                Global.group_size() == Int(1),
                basic_checks,
                Txn.sender() == App.globalGet(manager),
                Txn.application_args.length() == Int(4)
            )
        ),
        App.globalPut(current_tier, Add(App.globalGet(current_tier), Int(1))),
        App.globalPut(price, Btoi(Txn.application_args[1])),
        App.globalPut(minted_current_tier, Int(0)),
        App.globalPut(is_open, Int(0)),
        App.globalPut(tier_limit, Btoi(Txn.application_args[2])),
        App.globalPut(tier_limit_per_user, Btoi(Txn.application_args[3])),
        Approve()
    ])

    handle_open = Seq([
        Assert(
            And(
                Global.group_size() == Int(1),
                basic_checks,
                Txn.sender() == App.globalGet(manager),
            )
        ),
        App.globalPut(is_open, Int(1)),
        Approve()
    ])


    program = Cond(

                    [
                        Txn.application_id() == Int(0), on_deploy
                    ],
                    [
                        Txn.on_completion() == OnComplete.OptIn, handle_optin
                    ],
                    [
                        Txn.on_completion() == OnComplete.UpdateApplication, handle_update
                    ],
                    [
                        Txn.on_completion() == OnComplete.DeleteApplication, handle_delete
                    ],
                    [
                        Txn.application_args[0] == set_whitelist,
                        add_whitelist,
                    ],
                    [
                        Txn.application_args[0] == set_manager,
                        handle_set_manager,
                    ],
                    [
                        Txn.application_args[0] == buy, handle_payment
                    ],
                    [
                        Txn.application_args[0] == claim, handle_claim
                    ],
                    [
                        Txn.application_args[0] == increase_tier, handle_increase_tier
                    ],
                    [
                        Txn.application_args[0] == redeem, handle_redeem
                    ],
                    [
                        Txn.application_args[0] == open_minting, handle_open
                    ]
    )

    return program


if __name__ == "__main__":
    print(compileTeal(approval(), Mode.Application, version = 6))
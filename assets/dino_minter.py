from pyteal import *
from pyteal.ast.bytes import Bytes

def approval():
    PRICE_PER_UNIT = Int(100000000)
    DISCOUNT = Int(1000)
    MAX_UNITS = Int(1000)
    TIER_1_DISCOUNT = Int(10000000)
    TIER_2_DISCOUNT = Int(5000000)
    TIER_3_DISCOUNT = Int(2000000)
    TIER_4_DISCOUNT = Int(1000000)
    
    # locals
    whitelisted = Bytes("whitelisted")
    unclaimed_asset = Bytes("unclaimed")
    # globals
    minted_units = Bytes("minted_units")
    manager = Bytes("manager")
    whitelist_count = Bytes("whitelist_count")
    current_tier  = Bytes("current_tier")
    # Operations
    set_manager = Bytes("set_manager")
    give_discount = Bytes("give_discount")
    buy = Bytes("buy")
    claim = Bytes("claim")
    set_whitelist= Bytes("set_whitelist")
    redeem = Bytes("redeem")
    increase_tier = Bytes("increase_tier")
    #Scratch
    s = ScratchVar(TealType.uint64)
    asset = ScratchVar(TealType.uint64)


    @Subroutine(TealType.none)
    def increase_minted_units():
        incr_mint = App.globalGet(minted_units) + Int(1)
        return App.globalPut(minted_units, incr_mint)

    @Subroutine(TealType.none)
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

    @Subroutine(TealType.none)
    def transfer_asset(assetId):
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder().SetFields({
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: assetId,
                TxnField.asset_amount: Int(1),
                TxnField.asset_sender: Global.current_application_address(),
                TxnField.asset_receiver: Txn.sender()
            }),
            InnerTxnBuilder.Submit()
        ])


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

    
    @Subroutine(TealType.uint64)
    def compute_total_price(account):
        match App.localGet(account, whitelisted):
            case Int(1):
                return PRICE_PER_UNIT - TIER_1_DISCOUNT
            case Int(2):
                return PRICE_PER_UNIT - TIER_2_DISCOUNT
            case Int(3):
                return PRICE_PER_UNIT - TIER_3_DISCOUNT
            case Int(4):
                return PRICE_PER_UNIT - TIER_4_DISCOUNT
            case _:
                return PRICE_PER_UNIT


    basic_checks = And(
        Txn.rekey_to() == Global.zero_address(),
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.asset_close_to() == Global.zero_address(),
    )
    
    _checks = And(
        basic_checks,
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

    increase_tier = Seq([
        Assert(
            And(
                Global.group_size() == Int(1),
                Txn.sender() == App.globalGet(manager),
                App.globalGet(current_tier) <= Int(4)
                )
            ),
        App.globalPut(current_tier, App.globalGet(current_tier) + Int(1)),
        Approve()
    ])

    handle_optin = Seq([
        Assert(And(
            Global.group_size() == Int(1),
            Txn.application_args.length() == Int(0),
            basic_checks
        )),
        App.localPut(Txn.sender(), whitelisted, Int(0)),
        App.localPut(Txn.sender(), has_discount, Int(0)),
        App.localPut(Txn.sender(), unclaimed_asset, Int(0)),
        Approve(),
        
    ])

    handle_payment = Seq(
        Assert( Global.group_size() == Int(2)),
        s.store(compute_total_price(Gtxn[1].sender())),
        Assert(And(           
            Gtxn[1].type_enum() == TxnType().Payment,
            Gtxn[1].sender() == Gtxn[0].sender(),
            Gtxn[1].amount() >= s.load(),
            Gtxn[1].receiver() == Global.current_application_address(),
            App.localGet(Gtxn[1].sender(), whitelisted),
            App.localGet(Gtxn[1].sender(), whitelisted) == App.globalGet(current_tier)
        ))
        ,
        execute_mint_tx(Gtxn[0].application_args[1], Gtxn[0].application_args[2]),
        App.localPut(Gtxn[0].sender(), unclaimed_asset, asset.load()),
        increase_minted_units(),
        If(
            Gtxn[1].amount() > (s.load() + Global.min_txn_fee()),
            send_payment(Gtxn[1].sender(), (Gtxn[1].amount() - s.load() - Global.min_txn_fee()))
        ),
        If(
            App.localGet(Gtxn[1].sender(), has_discount) == Int(1),
            App.localPut(Gtxn[1].sender(), has_discount, Int(0))
        ),
        Approve()
    )

    handle_claim = Seq(
        Assert(
            Txn.assets[0] == App.localGet(Txn.sender(), unclaimed_asset)
        ),
        transfer_asset(App.localGet(Txn.sender(), unclaimed_asset)),
        Approve()
        )
    

    add_whitelist = Seq([
            Assert(And(
                Global.group_size() == Int(1),
                Txn.accounts.length() == Int(1),
                basic_checks,
                Txn.sender() == App.globalGet(manager),
            )),
            If(
                App.localGet(Txn.accounts[1], Bytes("whitelisted")) == Int(0),
                App.globalPut(whitelist_count, App.globalGet(whitelist_count) + Int(1)),
            ),

            App.localPut(Txn.accounts[1], Bytes("whitelisted"), Int(1)),
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
                        Txn.application_args[0] == redeem, handle_redeem
                    ],
    )

    return program


if __name__ == "__main__":
    print(compileTeal(approval(), Mode.Application, version = 6))
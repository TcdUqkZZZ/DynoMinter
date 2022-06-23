const { Runtime} = require('@algo-builder/runtime');
const { types } = require('@algo-builder/web');

const minBalance = BigInt(1e6);
const managerBalance = BigInt(10e6);
const amount = BigInt(1e6);


const MINTER = "dino_minter.py"
const CLEAR = "clear_state.py"

class Context {
    constructor(manager, buyer1, buyer2){
        this.manager = manager;
        this.buyer1 = buyer1;
        this.buyer2 = buyer2;
        this.runtime = new Runtime([manager, buyer1, buyer2])
        this.deployMinter(this.manager, MINTER, CLEAR);
        this.syncAccounts();
    }


    deployMinter(manager, minter, clear) {
        const appDef = {
            appName: "dinoMinter",
           metaType: types.MetaType.FILE,
            approvalProgramFilename: minter,
            clearProgramFilename: clear,            
            localInts:3,
            localBytes:0,
            globalInts:3,
            globalBytes:1,
        }

        this.App = this.runtime.deployApp(
            manager.account,
            appDef,
            { totalFee : 1000},
        )

        this.runtime.fundLsig(
            manager.account,
            this.App.applicationAccount,
            1e6
        )

   
    }

    syncAccounts() {
        this.manager = this.getAccount(this.manager.address);
        this.buyer1 = this.getAccount(this.buyer1.address);
        this.buyer2 = this.getAccount(this.buyer2.address);

    }

    getAccount(address) {
		return this.runtime.getAccount(address);
	}

    optIn(address){
        try {
             let receipt =this.runtime.optInToApp(
                address,
                this.App.appID,
                {},
                {},
                );
             return receipt
        } catch (e) {

        }
    }

    whitelist(manager, addrToWhitelist) {
		this.optIn(addrToWhitelist);
		_whitelist(this.runtime, manager, addrToWhitelist, this.App.appID);
	}

    setManager(manager, newPermManager) {
        this.optIn(newPermManager);
        _setManager(this.runtime, manager, newPermManager, this.App.appID)
    }

    giveDiscount(manager, buyerAddress) {
        _giveDiscount(this.runtime, manager, buyerAddress, this.App.appID)
    }

    buy(buyer, amount, url, metadata){
        return _buy(this.runtime, url, metadata, buyer, this.App.appID, amount)
    }

    claim(buyer){
        return _claim(this.runtime, buyer, this.App.appID)
    }

}

function _whitelist(runtime, manager, addrToWhiteList, appId){
    runtime.executeTx([{
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: manager,
        appID: appId,
        payFlags: { totalFee: 1000 },
        appArgs: ["str:set_whitelist"],
        accounts: [addrToWhiteList],
    },
]);
}

function _setManager(runtime, manager, newManager, appId){
    runtime.executeTx(
        [
            {
                type:types.TransactionType.CallApp,
                sign: types.SignType.SecretKey,
                fromAccount: manager,
                appID: appId,
                payFlags: {totalFee: 1000},
                appArgs: ["str:set_manager"],
                accounts: [newManager],
            }
        ]
    )
}

function _giveDiscount(runtime, manager, buyerAddress, appId){
    runtime.executeTx([{
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: manager,
        appID: appId,
        payFlags: {totalFee: 1000},
        appArgs: ["str:give_discount"],
        accounts: [buyerAddress],
    }
]);
}

function _buy(runtime,url, metadata, buyer, appId, amount){
    return runtime.executeTx([
    {
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: buyer,
        appID: appId,
        payFlags: {totalFee: 0},
        appArgs: ["str:buy",url, metadata],
    },
    {
        type: types.TransactionType.TransferAlgo,
        sign: types.SignType.SecretKey,
        fromAccount: buyer,
        appID: appId,
        amountMicroAlgos: amount,
        payFlags: {totalFee: 4000}
     }
    ])
}

function _claim(runtime, buyer, appId){

    console.log(buyer.getLocalState(appId, "unclaimed"))
    return runtime.executeTx([
    {
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: buyer.account,
        appID: appId,
        payFlags: {totalFee: 1000},
        appArgs: ["str:claim"],
        foreignAssets: [parseInt(buyer.getLocalState(appId, "unclaimed"))]
    }
        ]
    )
}



module.exports = {
	Context: Context,
};
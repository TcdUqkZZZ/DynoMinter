const { AccountStore } = require("@algo-builder/runtime");
const { types } = require("@algo-builder/web");
const { encodeAddress } = require("algosdk");
const { assert, Assertion, expect } = require("chai");
const { Context } = require("./lib");

const minBalance = BigInt(1e6);
const managerBalance = BigInt(10e6);

describe('dinoMinter test', () => {
    let manager, buyer1, buyer2
    let ctx
    function setUpCtx(){
        manager = new AccountStore(managerBalance);
        buyer1 = new AccountStore(minBalance);
        buyer2 = new AccountStore(minBalance);

        ctx = new Context(manager, buyer1, buyer2);
    }

    before( () => {
        setUpCtx();
        assert.isDefined(ctx.App)
        assert.notEqual(ctx.App.appID, 0)
    })

    it('Should let manager add addresses to whitelist', () => {
        assert.isDefined(ctx.manager.getApp(ctx.App.appID));
        ctx.optIn(ctx.buyer1.address);
       // ctx.syncAccounts();
        assert.isDefined(ctx.buyer1.getAppFromLocal(ctx.App.appID));

        assert.equal(ctx.buyer1.getLocalState(ctx.App.appID, "whitelisted"), 0n);


        const managerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );

        const managerAcct = ctx.getAccount(managerAddr);

        ctx.whitelist(
            managerAcct.account,
            ctx.buyer1.address,
            );


        ctx.syncAccounts();

        assert.equal(ctx.buyer1.getLocalState(ctx.App.appID, "whitelisted"), 1n);

    })

    it('Should set whitelist status to 0 upon opt-in', () => {
        ctx.optIn(ctx.buyer2.address);
        ctx.syncAccounts();
        assert.equal(ctx.buyer2.getLocalState(ctx.App.appID, "whitelisted"), 0n);
    })

    it('Should let manager pass its role onto others', () => {
        const oldManagerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );
        const managerAcct = ctx.getAccount(oldManagerAddr)
        ctx.setManager(managerAcct.account, ctx.buyer2.address);

        ctx.syncAccounts();

        const newManagerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );
        assert.notEqual(newManagerAddr, oldManagerAddr)
        assert.equal(newManagerAddr, ctx.buyer2.address)
    })

    it('Should NOT let unauthorized user change manager', () =>{
        assert.throws(() => {
            ctx.setManager(buyer1.account, buyer2.address)
        })
    })

    it('should let whitelisted user purchase token', () => {
        ctx.optIn(ctx.buyer1.address);
        const managerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );

        const managerAcct = ctx.getAccount(managerAddr);
        ctx.whitelist(
            managerAcct.account,
            ctx.buyer1.address,
            );

        ctx.increaseTier(managerAcct.account)
        ctx.buy(buyer1.account, managerAcct.account, 150000, "str:wegabibou", "str:belandijuliana")
        ctx.syncAccounts();
        assetId = parseInt(ctx.buyer1.getLocalState(ctx.App.appID, "unclaimed"))
        ctx.runtime.optIntoASA(assetId, buyer1.address, {})
        ctx.syncAccounts();
        ctx.claim(buyer1.account, assetId)
        assert.isNotEmpty(ctx.buyer1.assets, assetId)


    })

    it('should NOT let unwhitelisted user purchase token', () => {
        ctx.optIn(ctx.buyer2.address);
        const managerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );

        const managerAcct = ctx.getAccount(managerAddr);


        assert.throws( () => {
            ctx.buy(buyer2.account, managerAcct.account, 150000, "str:nope" , "str: nopenope")
        })
    })

    it('should let unwhitelisted user purchase token if sale is open', () => {
        ctx.optIn(ctx.buyer2.address);
        const managerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
        );

        const managerAcct = ctx.getAccount(managerAddr);

        ctx.open(managerAcct.account)

        ctx.buy(buyer2.account, managerAcct.account, 150000, "str:belandi" , "str: Ragassi")
        ctx.syncAccounts();
        assetId = parseInt(ctx.buyer2.getLocalState(ctx.App.appID, "unclaimed"))
        ctx.runtime.optIntoASA(assetId, buyer2.address, {})
        ctx.syncAccounts();
        ctx.claim(buyer2.account, assetId)
        ctx.syncAccounts();
        assert.isNotEmpty(ctx.buyer2.assets, assetId)
        
    })

    it('should refund appropriate amount if excess payment is made', () => {
        ctx.optIn(ctx.buyer1.address);
        
        const managerAddr = encodeAddress(
            ctx.runtime.getGlobalState(ctx.App.appID, "manager")
            );
            
            const managerAcct = ctx.getAccount(managerAddr);
            ctx.whitelist(
                managerAcct.account,
                ctx.buyer1.address,
                );
                
        ctx.syncAccounts()
        let initialBalance = ctx.buyer1.balance()
        let price = ctx.runtime.getGlobalState(ctx.App.appID, "price")
        let discount = price/10n
        ctx.buy(buyer1.account, managerAcct.account, price + BigInt(100000), "str:SPLAAASH", "str:{il gabibbo}")

        ctx.syncAccounts()
        let totalFees = 5000n
        let finalBalance = ctx.buyer1.balance()
        expect(BigInt(parseInt(initialBalance) - parseInt(finalBalance))).to.be.eq(price + totalFees - discount)
    })

})
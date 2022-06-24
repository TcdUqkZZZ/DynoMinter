const { types } = require("@algo-builder/web");

async function run(runtimeEnv, deployer) {
    const admin = deployer.accountsByName.get("admin");
    const buyer = deployer.accountsByName.get("buyer");

    const App = await deployer.getApp("dinoMinter");
    const appId = App.appID

    await deployer.optInAccountToApp(
        buyer,
        appId,
        { totalFee: 1000},
        {}
    )


    await deployer.executeTx({
        type: types.TransactionType.CallApp,
        sign: types.SignType.SecretKey,
        fromAccount: admin,
        appID: appId,
        payFlags: { totalFee: 1000 },
        appArgs: ["str:set_whitelist"],
        accounts: [buyer.addr],
    },
);

}

module.exports = {default: run};


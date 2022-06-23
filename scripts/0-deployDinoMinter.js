const { types } = require("@algo-builder/web");


async function run(runtimeEnv, deployer) {
    const admin = deployer.accountsByName.get("admin");
    const flags = {
        appName: "dinoMinter",
        metaType: types.MetaType.FILE,
        approvalProgramFilename: 'dino_minter.py',
        clearProgramFilename: 'clear_state.py',
        localInts:3,
        localBytes:0,
        globalInts:3,
        globalBytes:1,

    }

    let app = await deployer.deployApp(admin, flags, {totalFee: 1000})
    console.log(app)
}


module.exports = {default: run};
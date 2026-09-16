// JXA uninstaller: remove this build's plugins + registry entries.
// Usage: osascript -l JavaScript uninstall.js <experts_root> <config_dir>
//   <experts_root>: .../WorkBuddyExperts/experts  (manifest lists what we own)
//   <config_dir>:   ~/.workbuddy
ObjC.import('Foundation');
function read(p) {
  var s = ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null));
  return s || '';
}
function readJson(p) { var s = read(p).trim(); try { return s ? JSON.parse(s) : null; } catch (e) { return null; } }
function write(p, s) {
  $.NSString.alloc.initWithUTF8String(s).writeToFileAtomicallyEncodingError(p, true, $.NSUTF8StringEncoding, null);
}
var fm = $.NSFileManager.defaultManager;
function rmrf(p) { if (fm.fileExistsAtPath(p)) fm.removeItemAtPathError(p, null); }

function run(argv) {
  var expertsRoot = argv[0], config = argv[1];
  var manifest = readJson(expertsRoot + '/.codebuddy-plugin/marketplace.json') || {plugins: []};
  var market = config + '/plugins/marketplaces/my-experts';
  var cache = config + '/plugins/cache/my-experts';
  var removed = 0;
  manifest.plugins.forEach(function (p) {
    rmrf(market + '/plugins/' + p.name);
    rmrf(cache + '/' + p.name);
    removed++;
  });
  var inst = readJson(config + '/plugins/installed_plugins.json');
  if (inst && typeof inst === 'object') {
    Object.keys(inst).forEach(function (k) {
      if (k.indexOf('@my-experts') !== -1) delete inst[k];
    });
    write(config + '/plugins/installed_plugins.json', JSON.stringify(inst, null, 2) + '\n');
  }
  return 'uninstalled ' + removed + ' plugins. 重启 WorkBuddy 生效。';
}

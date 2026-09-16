// JXA helper for WorkBuddy Experts installer (macOS ships osascript; no python needed).
// Mirrors scripts/install.py behavior. Usage:
//   osascript -l JavaScript install.js list-plugins <marketplace_manifest>
//   osascript -l JavaScript install.js list-versions <experts_root>
//       -> "name\tversion" lines (version from each plugin's own plugin.json)
//   osascript -l JavaScript install.js merge-known <known_json> <market_name> <market_path>
//   osascript -l JavaScript install.js merge-installed <installed_json> <market> <cache_root> <experts_root> <name> <version>...
//   osascript -l JavaScript install.js strip-installed <installed_json> <market>
ObjC.import('Foundation');
function read(p) {
  var s = ObjC.unwrap($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null));
  return s || '';
}
function readJson(p) {
  var s = read(p).trim();
  if (!s) return null;
  try { return JSON.parse(s); } catch (e) { return null; }
}
function write(p, s) {
  $.NSString.alloc.initWithUTF8String(s).writeToFileAtomicallyEncodingError(p, true, $.NSUTF8StringEncoding, null);
}
function nowIso() { return new Date().toISOString().replace(/\.\d{3}Z$/, '.000Z'); }
function pluginVersion(expertsRoot, name) {
  var v = readJson(expertsRoot + '/plugins/' + name + '/.codebuddy-plugin/plugin.json');
  return (v && v.version) || '1.0.0';
}
function nowIso() { return new Date().toISOString().replace(/\.\d{3}Z$/, '.000Z'); }
function run(argv) {
  var mode = argv[0];
  if (mode === 'list-plugins') {
    var m = readJson(argv[1]) || {plugins: []};
    return (m.plugins || []).map(function (p) { return p.name; }).join('\n');
  }
  if (mode === 'list-versions') {
    var root = argv[1];
    var m2 = readJson(root + '/.codebuddy-plugin/marketplace.json') || {plugins: []};
    return (m2.plugins || []).map(function (p) {
      return (p.name || '') + '\t' + pluginVersion(root, p.name);
    }).join('\n');
  }
  if (mode === 'merge-known') {
    var knownPath = argv[1], mName = argv[2], mPath = argv[3];
    var known = readJson(knownPath) || {};
    known[mName] = {
      manifestName: mName, type: 'directory',
      source: {source: 'directory', path: mPath},
      installLocation: mPath,
      description: 'Marketplace from ' + mPath,
      lastUpdated: nowIso(), autoUpdate: false
    };
    write(knownPath, JSON.stringify(known, null, 2) + '\n');
    return 'known_marketplaces updated';
  }
  if (mode === 'merge-installed') {
    var instPath = argv[1], market = argv[2], cacheRoot = argv[3], expertsRoot = argv[4];
    var inst = readJson(instPath);
    if (!inst || typeof inst !== 'object') inst = {version: 2, plugins: {}};
    if (!inst.plugins) inst.plugins = {};
    for (var i = 5; i + 1 < argv.length; i += 2) {
      var name = argv[i], version = argv[i + 1];
      inst.plugins[name + '@' + market] = [{
        scope: 'user',
        installPath: cacheRoot + '/' + name + '/' + version,
        version: version, installedAt: nowIso(), lastUpdated: nowIso()
      }];
    }
    write(instPath, JSON.stringify(inst, null, 2) + '\n');
    return 'installed_plugins updated';
  }
  if (mode === 'strip-installed') {
    var p2 = argv[1], market2 = argv[2];
    var data = readJson(p2);
    if (data && data.plugins && typeof data.plugins === 'object') {
      Object.keys(data.plugins).forEach(function (k) {
        if (k.indexOf('@' + market2) !== -1) delete data.plugins[k];
      });
      write(p2, JSON.stringify(data, null, 2) + '\n');
    }
    return 'stripped';
  }
  return 'unknown mode';
}

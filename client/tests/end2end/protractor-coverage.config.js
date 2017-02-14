var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));
var q = require("q");
var FirefoxProfile = require("selenium-webdriver/firefox").Profile;

var makeFirefoxProfile = function (preferenceMap) {
  var profile = new FirefoxProfile();
  for (var key in preferenceMap) {
    profile.setPreference(key, preferenceMap[key]);
  }
  return q.resolve({
    browserName: "firefox",
    firefox_profile: profile
  });
};

// The test directory for downloaded files
var tmpDir = '/tmp/globaleaks-downloads';

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: false,
  directConnect: true,

  params: {
    'testFileDownload': true,
    'verifyFileDownload': true,
    'tmpDir': tmpDir
  },

  specs: specs,

  getMultiCapabilities: function() {
    return q.all([
      makeFirefoxProfile(
        {
          "intl.accept_language": "en_US",
          "browser.download.folderList": 2,
          "browser.download.dir": tmpDir,
          "browser.download.defaultFolder": tmpDir,
          "browser.download.downloadDir": tmpDir,
          "browser.download.lastDir": tmpDir,
          "browser.download.useDownloadDir": true,
          "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream",
          "browser.safebrowsing.enabled": false
        }
      )
    ]);
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 180000
  },

  plugins : [{
    path: '../../node_modules/protractor-istanbul-plugin'
  }]
};

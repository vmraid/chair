# Releasing VMRaid ERPAdda

* Make a new chair dedicated for releasing
```
chair init release-chair --vmraid-path git@github.com:vmraid/vmraid.git
```

* Get ERPAdda in the release chair
```
chair get-app erpadda git@github.com:vmraid/erpadda.git
```

* Configure as release chair. Add this to the common_site_config.json
```
"release_chair": true,
```

* Add branches to update in common_site_config.json
```
"branches_to_update": {
    "staging": ["develop", "hotfix"],
    "hotfix": ["develop", "staging"]
}
```

* Use the release commands to release
```
Usage: chair release [OPTIONS] APP BUMP_TYPE
```

* Arguments :
  * _APP_ App name e.g [vmraid|erpadda|yourapp]
  * _BUMP_TYPE_ [major|minor|patch|stable|prerelease]
* Options:
  * --from-branch git develop branch, default is develop
  * --to-branch git master branch, default is master
  * --remote git remote, default is upstream
  * --owner git owner, default is vmraid
  * --repo-name git repo name if different from app name
  
* When updating major version, update `develop_version` in hooks.py, e.g. `9.x.x-develop`

import requests
import yaml
import json
import os
import pathlib


def update_all():
    home = str(pathlib.Path(__file__).parent.resolve())
    for entry in os.listdir(f'{home}/config'):
        if not entry.endswith('.yaml'):
            print(f"Skipping non-YAML file: {entry}")
            continue
        try:
            path = os.path.join(f'{home}/config', entry)
            print(f'Updating modpack {entry.split('.')[0]}')
            with open(path, 'r') as config:
                config = yaml.safe_load(config)
            mods = config['mods']
            versions = config['versions']
            newest = 'nope'
            config['path'] = config['path'].replace('CURRENT', home)
            with requests.get(f"https://api.modrinth.com/v2/project/fabric-api") as req:
                if not req.ok:
                    print(f"Unable to get newest version")

                j = json.loads(req.content)
            for i in j['game_versions']:
                if i.startswith('1.'):
                    if not 'pre' in i and not 'rc' in i:
                        newest = i

            versions = [[newest, item[1]] if 'NEWEST' in item else item for item in versions]
            mods, old = update(mods, versions, get_old(config['path']))
            download(mods, config['path'], old)
        except Exception as e:
            print(f'Encountered Error while updating {entry}:\n{e}.'
                  f'\n Please check your configuration file and open an issue if the problem persists.')


def update(mods: list, aversions: list, old: list):
    to_update = []
    for mod in mods:
        versions = aversions.copy()
        with requests.get(f"https://api.modrinth.com/v2/project/{mod}/version") as req:
            if not req.ok:
                print(f"{mod} not found!")
                continue
            j = json.loads(req.content)
            for i in j:
                for version in versions:
                    if version[0] in i['game_versions']:
                        if version[1] in i['loaders']:
                            versions.remove(version)
                            if not i['files'][0]['filename'] in old[0]:
                                to_update.append(
                                    {'url': i['files'][0]['url'], 'name': i['files'][0]['filename'], 'version': version})
                            else:
                                index = old[0].index(i['files'][0]['filename'])
                                del old[0][index]
                                del old[1][index]
    return to_update, old


def download(mods, path, old) -> None:
    downoaded = 0
    deleted = 0
    for mod in mods:
        print(f'Downloading {mod["name"]} ({mod["version"]})...')
        if not os.path.isdir(f'{path}/{mod['version']}'):
            os.makedirs(f'{path}/{mod["version"]}')
        r = requests.get(mod['url'])
        if not r.ok:
            print(f'Error downloading {mod["name"]} ({mod["version"]})!')
            continue
        else:
            downoaded += 1
        with open(f'{path}/{mod['version']}/{mod['name']}', 'wb') as f:
            f.write(r.content)
    for i in range(len(old[0])):
        print(f'Deleting outdated version "{old[0][0]}"...')
        deleted += 1
        os.remove(f'{old[1][0]}/{old[0][0]}')
    if downoaded + deleted == 0:
        print('Successfully done nothing:)')
    else:
        print(f'Successfully downloaded {downoaded} updated mods and deleted {deleted} outdated mods!')


def get_old(path) -> list:
    f = []
    p = []
    print(f'Searching {path} for currently installed mods...')
    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            if file.endswith('.jar'):
                f.append(file)
                p.append(dirpath)
    print(f'Search complete! Found {len(f)} installed mods.')
    return [f, p]


if __name__ == '__main__':
    update_all()

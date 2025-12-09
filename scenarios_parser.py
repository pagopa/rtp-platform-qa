import argparse
import os

import yaml
from behave.model import Scenario
from behave.model import ScenarioOutline
from behave.parser import Parser

CLI = argparse.ArgumentParser()
CLI.add_argument(
    '--exclude-tags',
    nargs='*',
    type=str,
    default=['skip', 'need_fix']
)
CLI.add_argument(
    '--page-name',
    nargs=1,
    type=str,
)
CLI.add_argument(
    '--repo-name',
    nargs=1,
    type=str,
)
CLI.add_argument(
    '--root-dir',
    nargs=1,
    type=str,
)
CLI.add_argument(
    '--component-test-report',
    action='store_true'
)

args = CLI.parse_args()
excluded_tags = args.exclude_tags
print(f"Excluded tags: {excluded_tags}")

def parse_feature_files(feat_files):
    feature_scenarios = {}
    parser = Parser()

    for curr_feature_file in feat_files:
        with open(curr_feature_file, 'r') as f:
            feature_content = f.read()
            feature = parser.parse(feature_content, filename=curr_feature_file)
            scenarios = []

            for element in feature:
                if isinstance(element, (ScenarioOutline, Scenario)):
                    scenario_name = element.name
                    scenario_description = element.description
                    scenario_tags = element.tags
                    scenarios.append({
                        'name': scenario_name,
                        'description': scenario_description,
                        'tags': scenario_tags + feature.tags
                    })

            if scenarios:
                feature_file_name = os.path.splitext(os.path.basename(curr_feature_file))[0]
                feature_scenarios[feature_file_name] = {
                    'feature_name': feature.name,
                    'scenarios': scenarios,
                }

    return feature_scenarios


root_directory = args.root_dir[0]
feature_files = []
folder_links = []
component_features = {}

for dir in os.listdir(root_directory):
    if os.path.isdir(os.path.join(root_directory, dir)) and dir != 'steps' and dir != '__pycache__':
        folder_links.append(f"- [{dir}]({os.path.join('components', dir + '.md')})")
        component_features[dir] = []
        for root, _, files in os.walk(os.path.join(root_directory, dir)):
            for file in files:
                if file.endswith('.feature'):
                    feature_files.append(os.path.join(root, file))
                    component_features[dir].append(os.path.join(root, file))

all_scenarios = []
scenarios_by_feature = parse_feature_files(feature_files)

output_directory = 'docs/components'
os.makedirs(output_directory, exist_ok=True)

index_content = '# Components\n\n'
index_content += '\n'.join(folder_links) + '\n\n'
nav_links = []

for component, files in component_features.items():
    component_dir_path = os.path.join(output_directory, component)
    os.makedirs(component_dir_path, exist_ok=True)
    component_file_path = os.path.join(output_directory, f'{component}.md')
    with open(component_file_path, 'w') as component_file:
        component_file.write(f'# {component} features:\n\n')
        for file in files:
            feature_name = os.path.splitext(os.path.basename(file))[0]
            feature_data = scenarios_by_feature.get(feature_name, {})
            feature_title = feature_data.get('feature_name', feature_name)
            feature_file_path = os.path.join(component_dir_path, f'{feature_name}.md')
            component_file.write(f'## [{feature_title}]({os.path.join(component, feature_name + ".md")})\n\n')
            with open(feature_file_path, 'w') as feature_file:
                feature_file.write(f'# {feature_title}\n\n')
                feature_file.write(f'## Scenarios:\n\n')
                for scenario in feature_data.get('scenarios', []):
                    if not set(excluded_tags).intersection(set(scenario['tags'])):
                        all_scenarios.append(scenario['name'])
                        feature_file.write(f'* {scenario["name"]}\n')
        if args.component_test_report:
            component_file.write('<hr>\n')
            component_file.write(
                f'## [Allure BDD Test report](https://pagopa.github.io/{args.repo_name[0]}/bdd)'
            )

    nav_links.append({component: f'components/{component}.md'})

index_file_path = os.path.join('docs', 'index.md')
with open(index_file_path, 'w') as index_file:
    index_file.write(index_content)

mkdocs_config = {
    'site_name': args.page_name[0],
    'site_url': f'https://pagopa.github.io/{args.repo_name[0]}',
    'repo_name': f'pagopa/{args.repo_name[0]}',
    'repo_url': f'https://github.com/pagopa/{args.repo_name[0]}',
    'site_author': 'PagoPA',
    'use_directory_urls': True,
    'nav': [
        {'Home': 'index.md'},
        {'Components': nav_links},
        {'Allure Reports': [
            {'Functional': f'https://pagopa.github.io/{args.repo_name[0]}/functional'},
            {'BDD': f'https://pagopa.github.io/{args.repo_name[0]}/bdd'},
            {'UX': f'https://pagopa.github.io/{args.repo_name[0]}/ux'},
            {'Contract': f'https://pagopa.github.io/{args.repo_name[0]}/contract'},
        ]},
    ],
    'theme': {
        'name': 'material',
        'font': {'text': 'Roboto', 'code': 'Roboto Mono'},
    },
}

mkdocs_yaml_path = 'mkdocs.yml'
with open(mkdocs_yaml_path, 'w') as mkdocs_yaml:
    yaml.dump(mkdocs_config, mkdocs_yaml)

all_scenarios_file = os.path.join('docs', 'all_scenarios.txt')
with open(all_scenarios_file, 'w') as all_scenarios_file:
    all_scenarios_file.write('\n'.join(sorted(all_scenarios)))

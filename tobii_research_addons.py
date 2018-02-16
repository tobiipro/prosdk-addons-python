import source
from importlib import import_module

# Import all modules defined in source/__init__.py
for module in source.__all__:
    import_module("source." + module)

# Make all globals in each module global in this module.
for module_name, module_content in source.__dict__.items():
    if module_name in source.__all__:
        for global_name, global_value in module_content.__dict__.items():
            if not global_name.endswith('__'):  # Don't import built in functionality.
                globals()[global_name] = global_value

__copyright__ = '''
Copyright 2018 Tobii AB

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

# Clean up so we don't export these internally used variables.
del module_name
del module_content
del global_name
del global_value
del module
del import_module

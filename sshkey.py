#!/usr/bin/env python
# Linux setup utility
# Copyright (c) 2024 Jackson Tong, Creekside Networks LLC.

# SSH public key manager

import  json
import  simple_term_menu
from    global_config                    import GlobalConfig

def add_new_ssh_key():
    print ("\n o Adding a new key")

    # read existing ssh keys from the global configuration
    global_config = GlobalConfig()
    keys = global_config.get("ssh_keys")
    
    while True:
        new_ssh_key = input("   - Enter the ssh public key : ")

        key_parts = new_ssh_key.split()
        if len(key_parts) < 2:
            print("Invalid key format. Please enter a valid ssh public key.")
            continue

        break

    new_key_type  = key_parts[0]
    new_key_value = key_parts[1]
    new_key_name  = key_parts[2] if len(key_parts) > 2 else ""

    # now search if the key already exists
    if keys is not None:
        for key_name, key_data in keys.items():
            if new_key_value == key_data["key"]:
                print(f"     > Duplicate key detected. Key name: {key_name}")
                return key_name

    # get key name
    while True:
        new_key_name = input(f"   - Enter the ssh key name [{new_key_name}] : ") or new_key_name

        if not new_key_name:
            print("Key name cannot be empty.")
            continue

        if keys is not None and new_key_name in keys:
            print("Key name already exists. Please enter a unique key name.")
            continue

        break

    # Optionally, you can add the new key to the global configuration
    global_config.set(f"ssh_keys {new_key_name} type", new_key_type)
    global_config.set(f"ssh_keys {new_key_name} key", new_key_value)
    print("   - New key added successfully")
    return new_key_name

def retrieve_ssh_key():
    menu_entries = []
    # try to retrieve the list of ssh keys from the global configuration
    global_config = GlobalConfig()
    keys = global_config.get("ssh_keys")
    if keys is not None:
        for key in keys.keys():
            menu_entries.append(key)

    menu_entries.append("Add a new key")

    # preselect the "Add a new key" option if no keys are available
    default_index = menu_entries.index("Add a new key") if keys is None else 0

    terminal_menu = simple_term_menu.TerminalMenu(
        menu_entries, 
        title="- Choose SSH keys", 
        menu_cursor=">", 
        menu_cursor_style=("fg_red", "bold"), 
        menu_highlight_style=("bg_black", "fg_red"), 
        cycle_cursor=True,
        multi_select=True,
        show_multi_select_hint=True,
        preselected_entries=[default_index]
    )
    
    choosed_entries = terminal_menu.show()    
    if choosed_entries is not None:
        selected_keys = [menu_entries[i] for i in choosed_entries]
        #print("Selected SSH keys:", selected_keys)

        if "Add a new key" in selected_keys:
            new_key_name = add_new_ssh_key()

            if new_key_name not in selected_keys:
                selected_keys.append(new_key_name)

            selected_keys.remove("Add a new key")

        return selected_keys
    else:
        return None

if __name__ == "__main__":
    retrieve_ssh_key()
#!/bin/bash

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# ANSI Escape Codes for bold and reset
BOLD='\033[1m'
RESET='\033[0m'

if [ ! -d "docker_volume" ]; then
  mkdir "docker_volume"
  echo -e "   ${GREEN}Folder created:${BOLD}docker_volume${NC}"
  chmod 755 "docker_volume"
  echo -e "   ${GREEN}Permissions set to 755 for folder:${BOLD}docker_volume${NC}"
else
  echo -e "   ${GREEN}Folder already exists:${BOLD}docker_volume${NC}"
fi


if [ ! -d "docker_init" ]; then
  mkdir "docker_init"
  echo -e "   ${GREEN}Folder created:${BOLD}docker_init${NC}"
  chmod 755 "docker_init"
  echo -e "   ${GREEN}Permissions set to 755 for folder:${BOLD}docker_init${NC}"
else
  echo -e "   ${GREEN}Folder already exists:${BOLD}docker_init${NC}"
fi



# Define the directories where Volume folders are located

folder_names=("postgres_data" "pgadmin_data")

for folder_name in "${folder_names[@]}"; do
    # Check if the folder does not exist
    if [ ! -d "docker_volume/$folder_name" ]; then
        # Create the folder
        mkdir "docker_volume/$folder_name"
        echo -e "${GREEN}   Folder created: docker_volume/$folder_name${NC}"
    else
        echo -e "${GREEN}   Folder already exists: docker_volume/$folder_name${NC}"

    fi

    chmod -R 777 "docker_volume/$folder_name"
    echo -e "${GREEN}  Permissions set to 755 for folder:$folder_name${NC}"
done


# Define the directories where Dockerfiles are located
directories=("fastapi" "scheduler" "perfect_server")
for dir in "${directories[@]}"; do
  if [ -d "./$dir/.env" ]; then
    rm -r "./$dir/.env"
  fi
  cp .env ./$dir/
  
  if [ -f "./$dir/entrypoint.sh" ]; then
    chmod +x ./$dir/entrypoint.sh
  fi
done

done


#!/bin/bash

# Create directories if they don't exist
echo "Checking and creating required directories..."
mkdir -p ./tempo_data/wal ./tempo_data/blocks

# Set permissions
echo "Setting permissions to 777 for ./tempo_data..."
sudo chmod -R 777 ./tempo_data

echo ""
echo "--------------------------------------------"
echo "What do you want to do?"
echo "1) Run the application (docker-compose up --build)"
echo "2) Stop the application and remove volumes (docker-compose down -v)"
echo "3) Exit"
echo "--------------------------------------------"

read -p "Enter your choice [1/2/3]: " choice

case $choice in
    1)
        echo "Starting the application..."
        docker-compose --env-file=docker-compose-config.txt up --build -d
        echo "Application started"
        ;;
    2)
        echo "Stopping the application and removing volumes..."
        docker-compose --env-file=docker-compose-config.txt down -v
        echo "Application stopped"
        ;;
    3)
        echo "Exiting script."
        exit 0
        ;;
    *)
        echo "Invalid choice! Please run the script again and choose 1, 2, or 3."
        exit 1
        ;;
esac

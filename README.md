# 3rd-devs_exercises

## Overview

This is a repository containing exercises from an online course [AI_devs 3](https://www.aidevs.pl/). 

## Description

The project structure is as follows:
```
3rd-devs_exercises/
├── common/
│   ├── ngrok_utils.py
│   ├── openai_utils.py
│   ├── opencv_utils.py
│   └── ...
└── tasks/
    ├── task_1/
    ├── task_2/
    ├── ...
    └── task_20/
        ├── centrala_queries/
        ├── centrala_responses/
        ├── downloads/
        ├── openai_responses/
        ├── program_files/
        ├── prompts/
        └── task_20.py
```
where:
- common/ - contains common utilities for the project
- tasks/ - contains tasks from the course
- centrala_queries/ - contains queries to the AI devs server
- centrala_responses/ - contains responses from the AI devs server
- downloads/ - contains downloaded files
- openai_responses/ - contains responses from the OpenAI API
- program_files/ - contains files created by the program
- prompts/ - contains prompts for the OpenAI API
- task_X.py - contains the main program code for the task X

centrala_queries, centrala_responses and openai_responses directories are not included in the GitHub repository, because their contents are created dynamically during the execution of the program.

## Disclaimer

As the course progressed, my approach to solving the tasks changed. Therefore, the code in the repository is not always consistent. It results in that some tasks, especially the older ones, will run only when you checkout the corresponding commit, for example "add task 5" for task_5. I'm going to fix this issue soon.
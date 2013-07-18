mm
==========

`mm` is an executable that powers MavensMate Force.com IDEs. You can use `mm` to perform every important task relative to developing on the Force.com platform. For example, to compile a project:

```
$ mm -o compile_project
```

You can also use `mm` to provide a default UI for tasks like creating a new project, editing a project, running unit tests & anonymous apex, & deploying metadata to servers. Just use the --ui flag:

```
$ mm -o new_project --ui
```

In order to provide context to your operation, simply pipe json to `mm` via STDIN. For example:

```
$ mm -o compile_project <<< '{ "project_name" : "myproject" }'
```

### Command Line Arguments

```
-o : operation being requested (see full list of operations below)
-c : plugin client making the request ("Sublime Text" [default], "TextMate", "Notepad++", etc.)
```

### Supported Operations

#### new_project

```
{
	"project_name" 	: "myproject",
	"username" 		: "username@foo.com",
	"password" 		: "foo123"
	"package" 		: [
		"ApexClass" 	: "*",
		"ApexComponent" : ["MyComponent1", "MyComponent2"]
	]
}		
```

#### edit_project

> Modifies the contents of the project

```
{
	"project_name" 	: "myproject",
	"package" 		: [
		"ApexClass" 	: "*",
		"ApexComponent" : ["MyComponent1", "MyComponent2"]
	]
}		
```

#### compile_project

> Sends the entire project for compilation to the server

```
{
	"project_name" 	: "myproject"
}		
```

#### clean_project

> Reverts a project to server state based on package.xml

```
{
	"project_name" 	: "myproject"
}		
```

#### new_metadata

> Creates a new ApexClass, ApexPage, ApexComponent, ApexTrigger

```
{
	"project_name" 	: "myproject",
	"metadata_type"	: "ApexClass",
	"api_name" 		: "MyCoolClass"
}		
```

#### refresh

> Refreshes one or more files from the server

```
{
	"project_name"	: "myproject",
	"files" 		: ["/path/to/file/1", "/path/to/file/2"]
}		
```

#### compile

> Compiles one or more files to the server

```
{
	"project_name"	: "myproject",
	"files" 		: ["/path/to/file/1", "/path/to/file/2"]
}		
```

#### delete

> Deletes one or more files from the server

```
{
	"project_name"	: "myproject",
	"files" 		: ["/path/to/file/1", "/path/to/file/2"]
}		
```

#### get_active_session

> Retrieves an active session

```
{
	"username"		: "username@domain.com",
	"password" 		: "password123",
	"org_type" 		: "developer"
}		
```

#### execute_apex

```
{
    "project_name"    : "my project name"
	"debug_categories": [
     	{
       		"category": "Apex_code",
       		"level": "DEBUG"
     	},
     	{
       		"category": "Apex_profiling",
       		"level": "DEBUG"
     	}
	],
	"body"            : "String foo = 'bar';"
}
```

list of categories supported by MavensMate: 

```
'Db', 'Workflow', 'Validation', 'Callout', 'Apex_code', 'Apex_profiling'
```

list of levels supported by MavensMate: 

```
'None', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'FINE', 'FINER', 'FINEST'
```


#### update_credentials

```
{
	"project_name"	        : "myproject",
	"username"		: "username@domain.com",
	"password" 		: "password123",
	"org_type" 		: "developer"
}		
```

#### unit_test

```
{
    "classes" : [
        "UnitTestClass1", "UnitTestClass2"
    ],
    "run_all_tests" : false
}
```

#### deploy_to_server (or deploy)

```
{
    "check_only"            : true,
    "rollback_on_error"     : true,
    "destinations"          : [
        {
            "username"              : "username@domain.com",
            "org_type"              : "developer"
        }
    ],
    "package"               : {
        "ApexClass" : "*"
    }
}
```

#### list_metadata

```
{
    "sid"             : "",
    "metadata_type"   : "ApexClass",
    "murl"            : ""
}
```

#### index_metadata

```
{
	"project_name"	: "myproject"
}		
```

#### list_connections

```
{
	"project_name"	: "myproject"
}		
```

#### new_connection

```
{
	"project_name"	: "myproject",
	"username" 		: "username@domain.com",
	"password" 		: "foo123",
	"org_type" 		: "developer"
}		
```

#### delete_connection

```
{
	"project_name"	: "myproject",
	"id" 			: "connection_id"
}		
```

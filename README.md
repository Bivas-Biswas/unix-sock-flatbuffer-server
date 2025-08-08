# Unix Socket Flatbuffer Server


### How to run

1. Install libflatbuffers

```
sudo apt-get install libflatbuffers-dev
```

2. to generate the flatbuffer files

```
flatc --<lang> schema.fbs

<lang> = js, cpp, python
```

### How to run

#### Server.py

```
python server.py
```

### Client

1. CPP client

```
make
make run
```

2. Python client

```
python client.py
```

3. Node client

```
node client.js
```
import json
import yaml
from hammer.config.yaml2json import compare, convertArrays
from hammer.shell.yaml2json import load, save

# unittest suite for yaml2json
class TestYaml2Json:
    def test_load(self, tmpdir):
        with open(tmpdir + "/file.py", 'w') as f:
            f.write("some text here")
        c = load(tmpdir + "/file.py")
        assert c
        assert len(c) > 0
        assert c.find("some text here") != -1

    def test_save_load(self, tmpdir):
        c1 = "hello world"
        save(tmpdir + "/deleteme.txt", c1)
        c2 = load(tmpdir + "/deleteme.txt")
        assert c1 == c2

    def test_convert_arrays(self):
        o1 = {"foo":"bar", "sub": {0: "first", 1: "second"}}
        o2 = {"foo":"bar", "sub": {1: "first", 2: "second"}}
        otarget = {"foo":"bar", "sub": ["first", "second"]}
        assert convertArrays(o1) == otarget
        assert convertArrays(o2) == otarget

    def c(self, truth, o1, o2):
        #print(o1, o2)
        assert truth == compare(o1, o2)

    def ct(self, o1, o2):
        self.c(True, o1, o2)

    def cf(self, o1, o2):
        self.c(False, o1, o2)

    def test_compare(self):
        self.ct("1", "1")
        self.cf("1", "one")
        self.ct({}, {})
        self.ct([], [])
        self.cf({"x":[]}, {"x": None})
        self.ct({"x":[]}, {"x": []})
        self.ct({"x":{}}, {"x": {}})
        self.ct([{}, {}], [{}, {}])
        self.cf([{}, {}], [{}])
        self.ct({"foo":"bar"}, {"foo":"bar"})
        self.ct({"foo":"bar", "one":"1"}, {"foo":"bar", "one":"1"})
        self.ct({"foo":"bar", "one":"1"}, {"one":"1", "foo":"bar"})
        self.cf({"foo":"bar", "one":"1"}, {"one":1, "foo":"bar"})
        self.ct(["one"], ["one"])
        self.cf(["one"], ["1"])
        self.cf(["1"], [1])
        self.ct([1], [1])
        self.ct(["one", "two", "three"], ["one", "two", "three"])
        self.cf(["one", "two", "three"], ["one", "three", "two"])
        self.cf(["one", "two", "three"], ["one", "two"])

    exampleYaml = """
Projects:
  C/C++ Libraries:
  - libyaml       # "C" Fast YAML 1.1
  - Syck          # (dated) "C" YAML 1.0
  - yaml-cpp      # C++ YAML 1.1 implementation
  Ruby:
  - psych         # libyaml wrapper (in Ruby core for 1.9.2)
  - RbYaml        # YAML 1.1 (PyYaml Port)
  - yaml4r        # YAML 1.0, standard library syck binding
  Python:
  - PyYaml        # YAML 1.1, pure python and libyaml binding
  - PySyck        # YAML 1.0, syck binding
        """
    def test_convert(self):
        obj = yaml.safe_load(self.exampleYaml)
        obj = convertArrays(obj)
        outputContent = json.dumps(obj)
        obj2 = json.loads(outputContent)
        assert obj == obj2

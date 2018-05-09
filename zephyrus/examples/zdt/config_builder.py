from zephyrus.script import DefaultConfigBuilder

if __name__ == '__main__':
    import sys
    DefaultConfigBuilder().generate_config_file(sys.argv[1])

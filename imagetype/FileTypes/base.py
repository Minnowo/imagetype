class FileType(object):
    """
    Represents the file type object inherited by
    specific file type matchers.
    Provides convenient accessor and helper methods.
    """

    def __init__(self, mime, extension, extension_alternate=None):
        self.__mime = mime
        self.__extension = extension
        self.__extension_alternate = extension_alternate or []

    @property
    def mime(self):
        return self.__mime

    @property
    def extension(self):
        return self.__extension

    @property
    def extension_alternate(self):
        return self.__extension_alternate

    def is_extension(self, extension):
        return self.__extension is extension

    def is_mime(self, mime):
        return self.__mime is mime

    def match(self, buf):
        raise NotImplementedError

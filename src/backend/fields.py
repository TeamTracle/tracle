from django.db.models.fields.files import (
    FileField,
    FieldFile,
    ImageField,
    ImageFieldFile,
)


class WrappedFieldFile(FieldFile):
    def transfer(self):
        self.storage.transfer(self.name)


class WrappedFileField(FileField):
    attr_class = WrappedFieldFile


class WrappedImageFieldFile(ImageFieldFile):
    def transfer(self):
        self.storage.transfer(self.name)


class WrappedImageField(ImageField):
    attr_class = WrappedImageFieldFile

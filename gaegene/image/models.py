import logging
from StringIO import StringIO
import struct

from google.appengine.api import images, urlfetch
from google.appengine.ext import db

try:
    import png
except ImportError:
    png = None


def image_info(data):
    """
    Get the encoding, height, and width of the data (image bytes).
    Originally lifted from:
    http://groups.google.com/group/google-appengine/browse_thread/thread/cd287afcdf4cf976/388c5be1a22747fe
    """
    encoding = None
    height = None
    width = None
    try:
        w = h = None
        data = str(data)
        size = len(data)
        # handle GIFs
        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            encoding = None #App engine doesn't support GIF output
            w, h = struct.unpack("<HH", data[6:10])
        # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
        # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
        # and finally the 4-byte width, height
        elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
              and (data[12:16] == 'IHDR')):
            encoding = images.PNG
            w, h = struct.unpack(">LL", data[16:24])
        # Maybe this is for an older PNG version.
        elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
            encoding = images.PNG
            w, h = struct.unpack(">LL", data[8:16])
        # JPEGs! (Think: "Newman!")
        elif (size >= 2) and data.startswith('\377\330'):
            encoding = images.JPEG
            jpeg = StringIO(data)
            jpeg.read(2)
            b = jpeg.read(1)
            while (b and ord(b) != 0xDA):
                while (ord(b) != 0xFF): b = jpeg.read
                while (ord(b) == 0xFF): b = jpeg.read(1)
                if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                    jpeg.read(3)
                    h, w = struct.unpack(">HH", jpeg.read(4))
                    break
                else:
                    jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
                b = jpeg.read(1)
        width = int(w)
        height = int(h)
    except:
        pass
    return encoding, width, height


def retry_get(query, max_tries=3):
    tries = 0
    result = None
    while tries < max_tries:
        tries = tries + 1
        try:
            result = query.get()
            break
        except:
            if tries >= max_tries:
                raise
    return result


class GeneImage(db.Model):
    """
    A model to represent an image and its scaled/encoded versions.
    """
    name = db.StringProperty(required=True)
    image_bytes = db.BlobProperty(required=True)
    image_url = db.LinkProperty(required=False, default=None)
    master = db.SelfReferenceProperty(
        required=False, collection_name='transformed'
    )
    requested_width = db.IntegerProperty(required=False)
    requested_height = db.IntegerProperty(required=False)
    actual_width = db.IntegerProperty(required=False)
    actual_height = db.IntegerProperty(required=False)
    encoding = db.IntegerProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    
    def get_mime_type(self):
        return 'image/png' if self.encoding == images.PNG else 'image/jpeg'
    mime_type = property(get_mime_type)
    
    def get_or_create_image(
            self, width=None, height=None, encoding=None, max_tries=3
        ):
        # Get the master image
        master_image = self
        if self.master is not None:
            master_image = self.master
        # Make sure we're requesting integers
        try:
            width = int(width)
        except:
            width = None
        try:
            height = int(height)
        except:
            height = None
        # Make the request square if we only specify one dimension
        requested_width = width or height or master_image.actual_width
        requested_height = height or width or master_image.actual_height
        # Make sure we have valid encoding (default to the master's)
        if encoding != images.JPEG and encoding != images.PNG:
            encoding = master_image.encoding
        # Is the master the right size (actual)?
        if (requested_width == master_image.actual_width and
            requested_height == master_image.actual_height and
            encoding == master_image.encoding):
            return master_image
        # Is the master the right size (requested)?
        if (requested_width == master_image.requested_width and
            requested_height == master_image.requested_height and
            encoding == master_image.encoding):
            return master_image
        # Check the master's transformed images (requested)
        trans_images = master_image.transformed
        trans_images = trans_images.filter(
            'requested_width =', requested_width
        )
        trans_images = trans_images.filter(
            'requested_height =', requested_height
        )
        image = retry_get(trans_images.filter('encoding =', encoding))
        if image is None:
            trans_images = master_image.transformed
            trans_images = trans_images.filter(
                'actual_width =', requested_width
            )
            trans_images = trans_images.filter(
                'actual_height =', requested_height
            )
            image = retry_get(trans_images.filter('encoding =', encoding))
        if image is None:
            # Create the new transformed image
            new_name = "%s-%sx%s-%s" % (
                self.name, requested_width, requested_height, encoding
            )
            image = GeneImage.create(
                new_name, self.image_bytes,
                master=master_image,
                width=requested_width,
                height=requested_height,
                encoding=encoding
            )
        return image
    
    def get_pixels_boxed_row_flat_pixel(self, method='read'):
        """
        Returns the pixels of the image in boxed row flat pixel format.
        
        Only works if pypng is available and only for PNG files.
        """
        if png is None:
            raise NotImplementedError("pypng not found")
        if self.encoding != images.PNG:
            raise NotImplementedError("Only supported for PNG")
        reader = png.Reader(bytes=self.image_bytes)
        m = getattr(reader, method, None)
        width, height, pixels, metadata = m()
        return pixels
    
    @property
    def pixels(self):
        return self.get_pixels_boxed_row_flat_pixel()
    
    @property
    def pixels_asRGBA8(self):
        return self.get_pixels_boxed_row_flat_pixel(method='asRGBA8')
    
    def delete(self):
        if self.transformed is not None:
            for image in self.transformed:
                image.delete()
        try:
            super(GeneImage, self).delete()
        except:
            pass
    
    @classmethod
    def create(
            cls, name, image_bytes=None, image_url=None,
            master=None, width=None, height=None, encoding=None,
            key_name=None
        ):
        image = None
        try:
            if image_bytes is None and image_url is not None:
                image_bytes = urlfetch.fetch(image_url).content
            # Make it square if we only have one dimension
            width = width or height
            height = height or width
            # Get the image_bytes meta-data
            data_info = image_info(image_bytes)
            data_encoding = data_info[0]
            data_width = data_info[1]
            data_height = data_info[2]
            try:
                width = new_width = int(width)
                if data_width and new_width > data_width:
                    new_width = data_width
            except:
                width = new_width = data_width
            new_height = height
            try:
                height = new_height = int(height)
                if data_height and new_height > data_height:
                    new_height = data_height
            except:
                height = new_height = data_height
            new_encoding = encoding
            if new_encoding is None:
                new_encoding = data_encoding
            # Make it square if we only have one dimension
            new_width = new_width or new_height
            new_height = new_height or new_width
            # Can't resize if we don't have encoding and dimension
            if new_encoding is not None and new_width is not None:
                # Should we resize/reencode?
                if ((new_encoding != data_encoding) or
                    (new_width != data_width) or
                    (new_height != data_height)):
                    image_bytes = images.resize(
                        image_bytes,
                        width=new_width,
                        height=new_height,
                        output_encoding=new_encoding
                    )
                # Grab the new image info
                temp_image = images.Image(image_bytes)
                data_width = temp_image.width
                data_height = temp_image.height
            image = GeneImage(
                name=name,
                image_bytes=image_bytes,
                image_url=image_url,
                master=master,
                requested_width=width,
                requested_height=height,
                actual_width=data_width,
                actual_height=data_height,
                encoding=new_encoding,
                key_name=key_name
            )
            image.put()
        except Exception, e:
            logging.error("Failed to create image: %s" % str(e))
            if image and image.is_saved():
                try:
                    image.delete()
                except Exception, e2:
                    logging.error(
                        "Failed to delete error image: %s" % str(e2)
                    )
                image = None
        return image
    


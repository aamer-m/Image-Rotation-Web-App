from google.appengine.api import images
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.blobstore import BlobKey
import cStringIO
import PIL
from PIL import Image
from google.appengine.api import app_identity
from google.appengine.api import mail
import mimetypes
import webapp2

# To store the post parameters which are image, rotation angle and email-id
class ImageData(ndb.Model):
    imageKey = ndb.BlobKeyProperty()
    rotateAngle = ndb.IntegerProperty()
    emailId = ndb.StringProperty()

# Entry point of the application
class MainPage(webapp2.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload_photo')
        self.response.out.write('<html><head> <link type="text/css" rel="stylesheet" href="/stylesheets/style.css" /></head><body>')
        self.response.out.write("""
            <form action="{0}"
            enctype="multipart/form-data"
            method="post">
            <div id="center">
            <div><h3>Rotate Image and send to your email</h3></div>
            <div><label>Image:
            <input type="file" name="img" accept="image/*" required/></label></div>
            <div><label>Angle: <input type="number" name="rotateAngleDegrees" placeholder="Degrees" required/></label></div>
            <div><label>Email: <input type="email" name="emailId" placeholder="Email" required/></label></div>
            <div><input type="submit" value="Rotate Image"></div>
            </form>
            </body>
            </html>"""
        .format(upload_url))

# Hanlding upload image
class ImageUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        try:
            upload = self.get_uploads()[0]
            iR = ImageData(imageKey=upload.key(),
                           rotateAngle=int(self.request.get('rotateAngleDegrees')),
                           emailId=self.request.get('emailId'))
            iR.key = ndb.Key(ImageData, '123')
            iR.put()
            self.redirect('/view_photo/%s' % upload.key())
        except:
            self.error(500)

# Handling image manipulation and mail operation
class ImageDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
            if not blobstore.get(photo_key):
                self.error(404)
            else:
                # try:
                    blob_info = blobstore.BlobInfo.get(photo_key)
                    # blob_reader = blobstore.BlobReader(photo_key)
                    # image = blob_reader.read()

                    im = Image.open(blob_info.open())
                    _iR = ndb.Key(ImageData, '123').get()
                    # Image manipultaion
                    out = im.rotate(_iR.rotateAngle, resample=Image.BICUBIC, expand=True)
                    data = out
                    mimeType = im.format
                    buf = cStringIO.StringIO()
                    out.save(buf, mimeType)
                    data = buf.getvalue()

                    message = mail.EmailMessage(subject="Rotated Image")
                    
                    # print(app_identity.get_application_id())
                    # Sending mail after rotation
                    message.sender = "admin@" + app_identity.get_application_id() + ".appspotmail.com"
                    message.to = _iR.emailId
                    message.body = """
                    Hello

                    Check you rotated image in the attachment.

                    From RotateImage Team
                    """
                    message.html = """
                    <html><head></head><body>
                    Hello

                    Check you rotated image in the attachment.
                    <br>
                    From RotateImage Team
                    </body></html>
                    """
                    message.attachments = [('rotatedImage.' + mimeType, data)]
                    message.send()
                    ndb.Key(ImageData, '123').delete()
                    self.response.out.write('<html><head> <link type="text/css" rel="stylesheet" href="/stylesheets/style.css" /></head><body><div id="center">')
                    self.response.write("<div>Rotated image has been messaged to you</div>")
                    self.response.write("</div></body></html>")
                # except:
                    # self.error(500)

app = webapp2.WSGIApplication([
    ('/', MainPage), 
    ('/upload_photo', ImageUploadHandler),
    ('/view_photo/([^/]+)?', ImageDownloadHandler),
], debug=False)
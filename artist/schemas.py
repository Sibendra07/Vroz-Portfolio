#artist/schemas.py
#convert list into dict
def individual_sketch_dict(sketch):
      return {
         "id": str(sketch["_id"]),
         "title": sketch["title"],
         "description": sketch["description"],
         "image_url": sketch["image_url"],
         "video_url": sketch["video_url"],
         "sketch_url": sketch["sketch_url"],
         "for_sale": sketch["for_sale"],
         "is_sold": sketch["is_sold"],
         "price": sketch["price"],
         "is_deleted": sketch["is_deleted"],
         "created_at": sketch["created_at"],
         "updated_at": sketch["updated_at"]
      }

def all_sketches_dict(sketches):
      return [individual_sketch_dict(sketch) for sketch in sketches]
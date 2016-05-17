#!/usr/bin/env python

from NukeBoxDB import NukeBoxQuery


# #-----------------------------------------------------------------------#

# Create an Instance of the NukeBox Query Class
nbq = NukeBoxQuery()

# #-----------------------------------------------------------------------#
# #                        # CREATE TESTS BEGIN #
# #-----------------------------------------------------------------------#

# Create User Details
user_details = {'Model': 'Users',
                'name': 'Paul',
                'mac_id': '0987654321'
                }

# Get/Create User object
user_obj = nbq.create(user_details)

# Create File details
file_details = {'Model': 'Files',
                'path': '/home/music/what_went_down.mp3',
                'size': 10000,
                'filetype': 'mp3',
                'title': 'WHAT WENT DOWN',
                'artist': 'Foals',
                'genre': 'Indie',
                'album': 'WHAT WENT DOWN',
                'duration': '5:00',
                'user_id': user_obj.user_id
                }

# Get/Create the File object
file_obj = nbq.create(file_details)

# # Create Another File
# file_details = {'Model': 'Files',
#                 'path': '/home/music/birch_tree.mp3',
#                 'size': 12000,
#                 'filetype': 'mp3',
#                 'title': 'BIRCH TREE',
#                 'artist': 'Foals',
#                 'genre': 'Indie',
#                 'album': 'WHAT WENT DOWN',
#                 'duration': '5:10',
#                 'user_id': user_obj.user_id
#                 }

# # Get/Create the File object
# file_obj = nbq.create(file_details)

# #-----------------------------------------------------------------------#
# #                        # CREATE TESTS END #
# #-----------------------------------------------------------------------#

# #-----------------------------------------------------------------------#
# #                        # READ TESTS BEGIN #
# #-----------------------------------------------------------------------#

# # Remember, We can only filter on data that is Unique in our DB
# # Create the User Details dictionary
# user_details = {'Model': 'Users',
#                 'mac_id': '0987654321'
#                 }

# # Call to the Read Method
# u_result = nbq.read(**user_details)

# print(u_result.name, u_result.mac_id, u_result.user_id)

# # Create the File Details dictionary
# # Notice the 'user_id' key obtains its value from u_result
# file_details = {'Model': 'Files',
#                 'path': '/home/music/what_went_down.mp3',
#                 'title': 'WHAT WENT DOWN',
#                 }

# # Call to the Read Method
# f_result = nbq.read(**file_details)

# print(f_result.path, f_result.filetype, f_result.title)

# # Create f2 Details dictionary
# f2_details = {'Model': 'Files',
#               'title': 'BIRCH TREE'}

# # Call to the Read Method
# f2_result = nbq.read(**f2_details)

# print(f2_result.title)

# #-----------------------------------------------------------------------#
# #                        # READ TESTS END #
# #-----------------------------------------------------------------------#

# #-----------------------------------------------------------------------#
# #                        # UPDATE TESTS BEGIN #
# #-----------------------------------------------------------------------#

# # To update we must first pull an existing entry
# # To Pull the entry we must know the value of some unique param e.g title,
# # path, mac_id, path

# # Specify the Column to filter on & it's original value!
# update_file = {'Model': 'Files',
#                'column': 'title',
#                'value': 'WHAT WENT DOWN',
#                'title': 'what went down'
#                }

# # Call to the Update Method
# nbq.update(**update_file)

# update_user = {'Model': 'Users',
#                'column': 'mac_id',
#                'value': '0987654321',
#                'mac_id': '1234567890'
#                }

# # Call to the Update Method
# result = nbq.update(**update_user)
# if result:
#     print('Success')
# else:
#     print('Failed')
# #-----------------------------------------------------------------------#
# #                        # UPDATE TESTS END #
# #-----------------------------------------------------------------------#

# #-----------------------------------------------------------------------#
# #                        # DELETE TESTS BEGIN #
# #-----------------------------------------------------------------------#

# # Specify the Column to Delete on & it's value!
# delete_user = {'Model': 'Users',
#                'column': 'mac_id',
#                'value': '0987654321'
#                }

# # Call to the Delete Method
# result = nbq.delete(**delete_user)
# if result:
#     print('Success')
# else:
#     print('Failed')

# #-----------------------------------------------------------------------#
# #                        # DELETE TESTS END #
# #-----------------------------------------------------------------------#

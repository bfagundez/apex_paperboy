import lib.mm_util as util

def delete_metadata(client, metadata={}):
    print '>>> attempting to delete: ', metadata
    tmp, tmp_unpackaged = util.put_tmp_directory_on_disk(True)
    package_xml = util.get_package_xml_contents(metadata)
    util.put_package_xml_in_directory(tmp_unpackaged, package_xml, True)
    empty_package_xml = util.get_empty_package_xml_contents()
    util.put_empty_package_xml_in_directory(tmp_unpackaged, empty_package_xml)
    zip_file = util.zip_directory(tmp, tmp)
    delete_result = client.delete(zipFile=zip_file, rollbackOnError=True)
    util.delete_directory(tmp)
def get_file_url(url):
    filename = url.split("/")[-1]  # get the filename from the URL
    if "." not in filename:  # if there's no extension
        return url  # return the original URL
    # return the URL up to the query string, if present
    return url.split("?")[0]

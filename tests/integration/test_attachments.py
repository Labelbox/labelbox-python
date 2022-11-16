def test_create_attachments_without_names(datarow, image_url):
    attachment_content = {
        "IMAGE": image_url,
        "TEXT": "test-text",
        "IMAGE_OVERLAY": image_url,
        "HTML": image_url
    }

    for attachment_type, attachment_value in attachment_content.items():
        datarow.create_attachment(attachment_type, attachment_value)

    for attachment in datarow.attachments():
        assert attachment.attachment_type in attachment_content
        assert attachment_content[
            attachment.attachment_type] == attachment.attachment_value


def test_create_attachments_with_names(datarow, image_url):
    attachment_content = {
        "IMAGE": (image_url, "a"),
        "TEXT": ("test-text", "b"),
        "IMAGE_OVERLAY": (image_url, "c"),
        "HTML": (image_url, "d")
    }

    for attachment_type, (attachment_value,
                          attachment_name) in attachment_content.items():
        datarow.create_attachment(attachment_type, attachment_value,
                                  attachment_name)

    for attachment in datarow.attachments():
        assert attachment.attachment_type in attachment_content
        assert attachment_content[
            attachment.attachment_type][0] == attachment.attachment_value
        assert attachment_content[
            attachment.attachment_type][1] == attachment.attachment_name

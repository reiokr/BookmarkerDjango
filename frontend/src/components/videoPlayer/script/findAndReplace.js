import linkifyHtml from 'linkify-html'


const options = {
    attributes: null,
    className: null,
    defaultProtocol: 'http',
    events: null,
    format: (value, type) => value,
    formatHref: (href, type) => href,
    ignoreTags: [],
    nl2br: true,
    rel: null,
    tagName: 'a',
    target: null,
    truncate: 42,
    validate: true,
}

const useFindAndReplace = (comment) => {
    const regex = /(?:\d?\d:\d\d:?\d?\d?)/gm
    if (comment) {
        const newstr = comment.replace(
            regex,
            `<a class="timestamp" href="#">$&</a>`
        )
        const result = linkifyHtml(newstr, options)
        return result
    }
}

export {useFindAndReplace}
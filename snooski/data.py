
def convert_submission_to_obj(s):
    return {
        'title': s.title,
        'author': s.author.name,
        'comments': s.num_comments,
        'score': s.score,
        'subreddit': repr(s.subreddit),
        'visited': s.visited,
        'name': s.name,
        'id': s.id
    }

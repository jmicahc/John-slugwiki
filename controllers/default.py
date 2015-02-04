# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging


@auth.requires_login()
def create():
    """creates a new empty wiki page"""
    form = SQLFORM(db.page).process(next=URL('index'))
    return dict(form=form)
                  
def show():
    """shows a wiki page"""
    this_page = db.page(request.args(0,cast=int)) or redirect(URL('index'))
    db.post.page_id.default = this_page.id
    form = SQLFORM(db.post).process() if auth.user else None
    pagecomments = db(db.post.page_id==this_page.id).select()
    return dict(page=this_page, comments=pagecomments, form=form)


@auth.requires_login()
def edit():
    p = db.page(request.args(0,cast=int)) or redirect(URL('index'))
    form = SQLFORM(db.page, p).process(
        next = URL('show, args=request.args'))

def documents():
    p = db.page(request.args(0, cast=int)) or redirect(URL('index'))
    db.dumcent.page_id.default = page.id
    db.document.page_id.writable = False
    grid = SQLFORM.grid(db.document.page_id==page.id, args=[page.id])
    return dict(page=page, grid=grid)

#redirect(URL('default', 'index', args=[title], vars=dict(edit='y'))

def title():
    """
    This is the main page of the wiki.  
    You will find the title of the requested page in request.args(0).
    If this is None, then just serve the latest revision of something titled "Main page" or something 
    like that. 
    """
    response.title = ''
    title = request.args(0) or 'main page'
    display_title = title.title()

    
    if title=='main page':
       pages = db().select(db.pagetable.ALL)
       return dict(pages=pages)
    # You have to serve to the user the most recent revision of the 
    # page with title equal to title.
    
    # Let's uppernice the title.  The last 'title()' below
    # is actually a Python function, if you are wondering.
    display_title = title.title()


    
    # Here, I am faking it.  
    # Produce the content from real database data. 
    content = represent_wiki("I like <<Panda>>s")
    return dict(display_title=display_title, content=content)

def confirm():
    form = FORM.confirm("yes")
    title = request.args(0)
    if form.accepted:
        db.pagetable.insert(title=title)
        redirect(URL('default', 'index', args=[title]), vars=dict(edit='y'))
    else:
        redirect(URL('dfault', 'index', args=request.args))

def index():
    """
    This controller is here for testing purposes only.
    Feel free to leave it in, but don't make it part of your wiki.
    """
    response.title= ''
    title = request.args(0) or 'main page'
    display_title = title.title() # Uppernice the title

    if len(db(db.pagetable.title==title))==0:
        #display a confirmation form asking whether the user   
        #wants to create the page. If the user confirms, you
        #you need to have the user edit an empty revision. When
        #the revision is saved, create both the new page and the
        #innitial revision for the page.
        redirct(URL('default', 'confirm'), args=[title])
    else:
        #get the page id.
        page_id = db.pagetable(db.pagetable.title==title).select().first()

        #do a query on the revisions database for revisions matching page_id
        revisions_q = db.revisions(db.revisions.page_id==page_id)

        #find the most recient revision. This corresponds to revision with largest id.
        Max = db(revisions_q).select().first()
        for row in db(revisions_q).select():
            if row.id > Max.id:
               Max = row  #row of highest id.
        
        # get the content of the most recent revision.
        r = Max 
        s = r.body if r is not None else ''
        

        #Display the the page view {{=represent_wiki(revision_text}},
        #as noted in the main homeowrk page.
        form = None
        content = None

        # Are we editing?
        editing = request.vars.edit == 'true'

        # This is how you can use logging, very useful.
        logger.info("This is a request for page %r, with editing %r" %
                     (title, editing))
        if editing:
            # We are editing.  Gets the body s of the page.
            # Creates a form to edit the content s, with s as default.
            form = SQLFORM.factory(Field('body', 'text',
                                         label='Content',
                                         default=s
                                         ))
            # You can easily add extra buttons to forms.
            form.add_button('Cancel', URL('default', 'index'))
            # Processes the form.
            if form.process().accepted:
                db.revision.insert(ref=page_id, body=form.vars.body)
                redirect(URL('default', 'index', args=request.args))
            content = form
        else:
            # We are just displaying the page
            content = s
        return dict(display_title=display_title, content=content, editing=editing)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)

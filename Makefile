# common config macros (changing)
GTAG = devel
#GTAG = roybranch
#GTAG = devel
#GTAG = master
OS_VERSION = 18.04
R_VERSION=3.6.3
MKL_VERSION = 2020.1.217
RS_VERSION=1.2.1335
DEVEL_VERSION = 2.8.0
MASTER_VERSION = 2.8.0


# other common macros (not changing much)
DC = docker
DB = $(DC) build
D_REP = uwgac
DO_FLAGS =
ifdef $(USECACHE)
	CACHE_OPT =
else
	CACHE_OPT = --no-cache
endif

# base name macros
DB_OPTS = $(DO_FLAGS) $(CACHE_OPT)
DB_LINUX = ubuntu
DB_OS = $(DB_LINUX)-$(OS_VERSION)-hpc
DB_R = r-mkl
DB_TM = topmed
DB_APPS = apps
DB_PKGS = tm-rpkgs
DB_RS = tm-rstudio

# macros of docker build file names
DF_OS = $(DB_OS).dfile
DF_APPS = $(DB_APPS).dfile
DF_R = $(DB_R).dfile
DF_PKGS_MASTER = $(DB_PKGS)-master.dfile
DF_PKGS_DEVEL = $(DB_PKGS)-devel.dfile
DF_TM = $(DB_TM).dfile
DF_RS = $(DB_RS).dfile

# macros of docker image tags
DT_OS = 06.24.2020
DT_R = $(R_VERSION)
DT_APPS = 06.24.2020
DT_PKG_MASTER = $(MASTER_VERSION)
DT_PKG_DEVEL = $(DEVEL_VERSION)
DT_TM_MASTER = $(MASTER_VERSION)
DT_TM_DEVEL = $(DEVEL_VERSION)
DT_RS = $(RS_VERSION)

# macros of docker image names
DI_OS = $(DB_OS)
DI_R = r-$(R_VERSION)-mkl
DI_APPS = $(DB_APPS)
DI_PKGS_MASTER = $(DB_PKGS)-master
DI_PKGS_DEVEL = $(DB_PKGS)-devel
DI_PKGS_GTAG = $(DB_PKGS)-$(GTAG)
DI_TM = $(DB_TM)-$(GTAG)
DI_RS = $(DB_RS)-$(GTAG)
D_IMAGES = $(DI_OS) $(DI_APPS) $(DI_R) $(DI_PKGS_GTAG) $(DI_TM) $(DI_RS)
D_ALL_IMAGES = $(addsuffix .image,$(D_IMAGES))
D_PUSH = $(addsuffix .push,$(D_IMAGES))
# summary
ifeq ($(GTAG),master)
	TM_BASENAME=$(DI_PKGS_MASTER)
	PKG_DEPEND=$(DI_PKGS_MASTER)
	DT_IMAGE=$(DT_TM_MASTER)
	DT_PACKAGE=$(DT_PKG_MASTER)
else ifeq ($(GTAG),devel)
	TM_BASENAME=$(DI_PKGS_DEVEL)
	PKG_DEPEND=$(DI_PKGS_DEVEL)
	DT_IMAGE=$(DT_TM_DEVEL)
	DT_PACKAGE=$(DT_PKG_DEVEL)
else ifeq ($(GTAG),roybranch)
	TM_BASENAME=$(DI_PKGS_DEVEL)
	PKG_DEPEND=$(DI_PKGS_DEVEL)
	DI_PKGS_GTAG=$(DI_PKGS_DEVEL)
	DT_IMAGE=$(DT_TM_DEVEL)
	DT_PACKAGE=$(DT_PKG_DEVEL)
else
	TM_BASENAME=$(DI_PKGS_DEVEL)
	PKG_DEPEND=$(DI_PKGS_DEVEL)
	DI_PKGS_GTAG=$(DI_PKGS_DEVEL)
	DT_IMAGE=$(DT_TM_DEVEL)
	DT_PACKAGE=$(DT_PKG_DEVEL)
	GTAG=roybranch
endif

# do stuff
.PHONY:  all

all: $(D_ALL_IMAGES)
	@echo ">>> Build is complete"

push: $(D_PUSH)
	@echo ">>> Push is complete"

$(DI_OS).image: $(DF_OS)
	@echo ">>> "Building $(D_REP)/$(DI_OS):$(DT_OS)
	$(DB) -t $(D_REP)/$(DI_OS):$(DT_OS) $(DB_OPTS) --build-arg base_os=$(DB_LINUX) \
        --build-arg mkl_version=$(MKL_VERSION) --build-arg itag=$(OS_VERSION) -f $(DF_OS) . > build_$(DI_OS).log
	$(DC) tag $(D_REP)/$(DI_OS):$(DT_OS) $(D_REP)/$(DI_OS):latest
	touch $(DI_OS).image

$(DI_APPS).image: $(DF_APPS) $(DI_OS).image
	@echo ">>> "Building $(D_REP)/$(DI_APPS):$(DT_APPS)
	$(DB) -t $(D_REP)/$(DI_APPS):$(DT_APPS) $(DB_OPTS) \
        --build-arg base_name=$(DI_OS) \
        --build-arg itag=latest -f $(DF_APPS) . > build_$(DI_APPS).log
	$(DC) tag $(D_REP)/$(DI_APPS):$(DT_APPS) $(D_REP)/$(DI_APPS):latest
	touch $(DI_APPS).image

$(DI_R).image: $(DF_R) $(DI_APPS).image
	@echo ">>> "Building $(D_REP)/$(DI_R):$(DT_R)
	$(DB) -t $(D_REP)/$(DI_R):$(DT_R) $(DB_OPTS) \
        --build-arg ra_version=$(R_VERSION) --build-arg base_name=$(DI_APPS) \
        --build-arg itag=latest -f $(DF_R) . > build_$(DI_R).log
	$(DC) tag $(D_REP)/$(DI_R):$(DT_R) $(D_REP)/$(DI_R):latest
	touch $(DI_R).image

$(DI_PKGS_MASTER).image: $(DF_PKGS_MASTER) $(DI_R).image
	@echo ">>> "Building $(D_REP)/$(DI_PKGS_MASTER):$(DT_PACKAGE) from git branch master
	$(DB) -t $(D_REP)/$(DI_PKGS_MASTER):$(DT_PACKAGE) $(DB_OPTS) \
        --build-arg r_version=$(R_VERSION) --build-arg base_name=$(DI_R) \
        --build-arg itag=latest --build-arg git_branch=master \
        -f $(DF_PKGS_MASTER) . > build_$(DI_PKGS_MASTER).log
	$(DC) tag $(D_REP)/$(DI_PKGS_MASTER):$(DT_PACKAGE) $(D_REP)/$(DI_PKGS_MASTER):latest
	touch $(DI_PKGS_MASTER).image

$(DI_PKGS_DEVEL).image: $(DF_PKGS_DEVEL) $(DI_PKGS_MASTER).image
	@echo ">>> "Building $(D_REP)/$(DI_PKGS_DEVEL):$(DT_PKG_DEVEL) from git branch devel
	$(DB) -t $(D_REP)/$(DI_PKGS_DEVEL):$(DT_PKG_DEVEL) $(DB_OPTS) \
        --build-arg r_version=$(R_VERSION) --build-arg base_name=$(DI_PKGS_MASTER) \
        --build-arg itag=latest --build-arg git_branch=devel \
        -f $(DF_PKGS_DEVEL) . > build_$(DI_PKGS_DEVEL).log
	$(DC) tag $(D_REP)/$(DI_PKGS_DEVEL):$(DT_PKG_DEVEL) $(D_REP)/$(DI_PKGS_DEVEL):latest
	touch $(DI_PKGS_DEVEL).image

$(DI_TM).image: $(DF_TM) $(PKG_DEPEND).image
	@echo ">>> "Building $(D_REP)/$(DI_TM):$(DT_IMAGE) from git branch $(GTAG)
	$(DB) -t $(D_REP)/$(DI_TM):$(DT_IMAGE) $(DB_OPTS)  \
        --build-arg base_name=$(TM_BASENAME) --build-arg itag=latest \
        --build-arg git_branch=$(GTAG) -f $(DF_TM) . > build_$(DI_TM).log
	$(DC) tag $(D_REP)/$(DI_TM):$(DT_IMAGE) $(D_REP)/$(DI_TM):latest
	touch $(DI_TM).image

$(DI_RS).image: $(DF_RS) $(DI_TM).image
ifeq ($(GTAG),devel)
	@echo ">>> "Building $(D_REP)/$(DI_RS):$(DT_RS) from git branch $(GTAG)
	$(DB) -t $(D_REP)/$(DI_RS):$(DT_RS) $(DB_OPTS)  \
        --build-arg rs_version=$(RS_VERSION) --build-arg base_name=$(DI_TM) \
        --build-arg itag=latest -f $(DF_RS) . > build_$(DI_RS).log
	$(DC) tag $(D_REP)/$(DI_RS):$(DT_RS) $(D_REP)/$(DI_RS):latest
	touch $(DI_RS).image
else
	@echo ">>> "Build $(DI_RS) only for devel branch
endif

.SUFFIXES : .dfile2 .image .push

.image.push:
	@echo ">>> pushing $(D_REP)/$*"
	$(DC) push $(D_REP)/$*
	@touch $@

.dfile2.image:
	@echo ">>> building $(D_REP)/$*:$(D_TAG) $< "
	$(DB) -t $(D_REP)/$*:$(D_TAG) $(DB_FLAGS) -f $< . > build_$*.log
	@touch $@

clean:
	@echo Deleting all images $(D_IMAGES_IMG)
	@rm -f $(D_IMAGES_IMG)
	@echo Deleting all pushes $(D_PUSH)
	@rm -f $(D_PUSH)
	@echo Deleting all logs
	@rm -f *.log

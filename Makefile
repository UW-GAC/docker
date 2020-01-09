# common config macros (changing)
GTAG = devel
#GTAG = roybranch
#GTAG = devel
#GTAG = master
OS_VERSION = 18.04
R_VERSION=3.6.1
MKL_VERSION = 2019.2.187
RS_VERSION=1.2.1335
DTAG = 2.6

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
DF_PKGS = $(DB_PKGS).dfile
DF_TM = $(DB_TM).dfile
DF_RS = $(DB_RS).dfile

# macros of docker image tags
DT_OS = $(DTAG)
DT_R = $(DTAG)
DT_APPS = $(DTAG)
DT_PKGS = $(DTAG)
DT_TM = $(DTAG)
DT_RS = $(DTAG)

# macros of docker image names
DI_OS = $(DB_OS)
DI_R = r-$(R_VERSION)-mkl
DI_APPS = $(DB_APPS)
DI_PKGS = $(DB_PKGS)-$(GTAG)
DI_TM = $(DB_TM)-$(GTAG)
DI_RS = $(DB_RS)-$(GTAG)
D_IMAGES = $(DI_OS) $(DI_APPS) $(DI_R) $(DI_PKGS) $(DI_TM) $(DI_RS)
D_ALL_IMAGES = $(addsuffix .image,$(D_IMAGES))
D_PUSH = $(addsuffix .push,$(D_IMAGES))
# summary
ifeq ($(GTAG),master)
	TM_BASENAME=$(DI_PKGS)
	RS_BASENAME=
else ifeq ($(GTAG),devel)
	TM_BASENAME=$(DI_PKGS)
else ifeq ($(GTAG),roybranch)
	TM_BASENAME=$(DB_PKGS)-devel
else ifeq ($(GTAG),python3)
	TM_BASENAME=$(DB_PKGS)-devel
else
	TM_BASENAME=$(DB_PKGS)-devel
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
        --build-arg r_version=$(R_VERSION) --build-arg base_name=$(DI_APPS) \
        --build-arg itag=latest -f $(DF_R) . > build_$(DI_R).log
	$(DC) tag $(D_REP)/$(DI_R):$(DT_R) $(D_REP)/$(DI_R):latest
	touch $(DI_R).image

$(DI_PKGS).image: $(DF_PKGS) $(DI_R).image
ifeq ($(GTAG),roybranch)
	@echo ">>> "Building R packages for git branch $(GTAG) is not needed
	touch $(DI_PKGS).image
else ifeq ($(GTAG),python3)
	@echo ">>> "Building R packages for git branch $(GTAG) is not needed
	touch $(DI_PKGS).image
else
	@echo ">>> "Building $(D_REP)/$(DI_PKGS):$(DT_PKGS) from git branch $(GTAG)
	$(DB) -t $(D_REP)/$(DI_PKGS):$(DT_PKGS) $(DB_OPTS) \
        --build-arg r_version=$(R_VERSION) --build-arg base_name=$(DI_R) \
        --build-arg itag=latest --build-arg git_branch=$(GTAG) \
        -f $(DF_PKGS) . > build_$(DI_PKGS).log
	$(DC) tag $(D_REP)/$(DI_PKGS):$(DT_PKGS) $(D_REP)/$(DI_PKGS):latest
	touch $(DI_PKGS).image
endif

$(DI_TM).image: $(DF_TM) $(DI_PKGS).image
	@echo ">>> "Building $(D_REP)/$(DI_TM):$(DT_TM) from git branch $(GTAG)
	$(DB) -t $(D_REP)/$(DI_TM):$(DT_TM) $(DB_OPTS)  \
        --build-arg base_name=$(TM_BASENAME) --build-arg itag=latest \
        --build-arg git_branch=$(GTAG) -f $(DF_TM) . > build_$(DI_TM).log
	$(DC) tag $(D_REP)/$(DI_TM):$(DT_TM) $(D_REP)/$(DI_TM):latest
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

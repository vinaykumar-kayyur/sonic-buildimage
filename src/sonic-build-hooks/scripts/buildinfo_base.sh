#!/bin/bash

BUILDINFO_PATH=/usr/local/share/buildinfo

LOG_PATH=$BUILDINFO_PATH/log
VERSION_PATH=$BUILDINFO_PATH/versions
PRE_VERSION_PATH=$BUILDINFO_PATH/pre-versions
DIFF_VERSION_PATH=$BUILDINFO_PATH/diff-versions
BUILD_VERSION_PATH=$BUILDINFO_PATH/build-versions
POST_VERSION_PATH=$BUILDINFO_PATH/post-versions
VERSION_DEB_PREFERENCE=$BUILDINFO_PATH/versions/01-versions-deb
WEB_VERSION_FILE=$VERSION_PATH/versions-web
BUILD_WEB_VERSION_FILE=$BUILD_VERSION_PATH/versions-web
REPR_MIRROR_URL_PATTERN='http:\/\/packages.trafficmanager.net\/debian'
DPKG_INSTALLTION_LOCK_FILE=/tmp/.dpkg_installation.lock
GIT_VERSION_FILE=$VERSION_PATH/versions-git
BUILD_GIT_VERSION_FILE=$BUILD_VERSION_PATH/versions-git

. $BUILDINFO_PATH/config/buildinfo.config
if [ -e /vcache ]; then
	PKG_CACHE_PATH=/vcache/${IMAGENAME}
else
	PKG_CACHE_PATH=/sonic/target/vcache/${IMAGENAME}
fi
PKG_CACHE_FILE_NAME=${PKG_CACHE_PATH}/cache.tgz
mkdir -p ${PKG_CACHE_PATH}

. $BUILDINFO_PATH/scripts/utils.sh


URL_PREFIX=$(echo "${PACKAGE_URL_PREFIX}" | sed -E "s#(//[^/]*/).*#\1#")

if [ "$(whoami)" != "root" ] && [ -n "$(which sudo)" ];then
    SUDO=sudo
else
    SUDO=''
fi

log_err()
{
    echo "$(date "+%F-%H-%M-%S") ERR $1" >> $LOG_PATH/error.log
    echo "$1" 1>&2
}
log_info()
{
    echo "$(date "+%F-%H-%M-%S") INFO $1" >> $LOG_PATH/info.log
    echo "$1" 1>&2
}


# Get the real command not hooked by sonic-build-hook package
get_command()
{
    # Change the PATH env to get the real command by excluding the command in the hooked folders
    local path=$(echo $PATH | sed 's#[^:]*buildinfo/scripts:##' | sed "s#/usr/local/sbin:##")
    local command=$(PATH=$path which $1)
    echo $command
}

check_version_control()
{
    # The env variable SONIC_VERSION_CONTROL_COMPONENTS examples:
    # all            -- match all components
    # py2,py3,deb    -- match py2, py3 and deb only
    if [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,all,* ]] || [[ ",$SONIC_VERSION_CONTROL_COMPONENTS," == *,$1,* ]]; then
        echo "y"
    else
        echo "n"
    fi
}

get_url_version()
{
    local package_url=$1
    /usr/bin/curl -Lks $package_url | md5sum | cut -d' ' -f1
}

check_if_url_exist()
{
    local url=$1
    if /usr/bin/curl --output /dev/null --silent --head --fail "$1" > /dev/null 2>&1; then
        echo y
    else
        echo n
    fi
}

get_version_cache_option()
{
	#SONIC_VERSION_CACHE="cache"
	if [ ! -z ${SONIC_VERSION_CACHE} ]; then
		if [ ${SONIC_VERSION_CACHE} == "rcache" ]; then
			echo -n "rcache"
		elif [ ${SONIC_VERSION_CACHE} == "wcache" ]; then
			echo -n "wcache"
		elif [ ${SONIC_VERSION_CACHE} == "cache" ]; then
			echo -n  "wcache"
		else
			echo -n ""
			return 1
		fi
		echo -n ""
		return 0
	fi
	echo -n ""
	return 1
}


# Enable or disable the reproducible mirrors
set_reproducible_mirrors()
{
    # Remove the charater # in front of the line if matched
    local expression="s/^#\(.*$REPR_MIRROR_URL_PATTERN\)/\1/"
    if [ "$1" = "-d" ]; then
        # Add the charater # in front of the line if match
        expression="s/^deb.*$REPR_MIRROR_URL_PATTERN/#\0/"
    fi

    local mirrors="/etc/apt/sources.list $(find /etc/apt/sources.list.d/ -type f)"
    for mirror in $mirrors; do
        $SUDO sed -i "$expression" "$mirror"
    done
}

download_packages()
{
    local parameters=("$@")
    local filenames=
    declare -A filenames
    declare -A SRC_FILENAMES
    local url=
    local real_version=
    local SRC_FILENAME=
    local DST_FILENAME=

    for (( i=0; i<${#parameters[@]}; i++ ))
    do
        local para=${parameters[$i]}
        local nexti=$((i+1))
        if [[ "$para" == -o || "$para" == -O ]]; then
			DST_FILENAME=${parameters[$nexti]}
        elif [[ "$para" == *://* ]]; then
            local url=$para
            local real_version=

            # Skip to use the proxy, if the url has already used the proxy server
            if [[ $url == ${URL_PREFIX}* ]]; then
                continue
            fi
			local result=0
			WEB_CACHE_PATH=${PKG_CACHE_PATH}/web
			mkdir -p ${WEB_CACHE_PATH}
			local WEB_FILENAME=$(echo $url | awk -F"/" '{print $NF}' | cut -d? -f1 | cut -d# -f1)
			if [ -z "${DST_FILENAME}" ];then
				DST_FILENAME=${WEB_FILENAME}
			fi
			local VERSION=$(grep "^${url}=" $WEB_VERSION_FILE | awk -F"==" '{print $NF}')
			if [ ! -z "${VERSION}" ]; then

				if [ "$ENABLE_VERSION_CONTROL_WEB" == y ]; then
					if [ ! -z "$(get_version_cache_option)" ]; then
						SRC_FILENAME=${WEB_CACHE_PATH}/${WEB_FILENAME}-${VERSION}.tgz
						if [ -f ${SRC_FILENAME} ]; then
							log_info "Loading from web cache URL:${url}, SRC:${SRC_FILENAME}, DST:${DST_FILENAME}"
							cp ${SRC_FILENAME} ${DST_FILENAME}
							touch ${SRC_FILENAME}
							continue
						fi
					fi
				fi
			fi

            if [ "$ENABLE_VERSION_CONTROL_WEB" == y ]; then
                local version=
                local filename=$(echo $url | awk -F"/" '{print $NF}' | cut -d? -f1 | cut -d# -f1)
                [ -f $WEB_VERSION_FILE ] && version=$(grep "^${url}=" $WEB_VERSION_FILE | awk -F"==" '{print $NF}')
                if [ -z "$version" ]; then
                    log_err "Warning: Failed to verify the package: $url, the version is not specified" 1>&2
                    continue
                fi

                local version_filename="${filename}-${version}"
                local proxy_url="${PACKAGE_URL_PREFIX}/${version_filename}"
                local url_exist=$(check_if_url_exist $proxy_url)
                if [ "$url_exist" == y ]; then
                    parameters[$i]=$proxy_url
                    filenames[$version_filename]=$filename
                    real_version=$version
                else
                    real_version=$(get_url_version $url)
                    if [ "$real_version" != "$version" ]; then
                        log_err "Failed to verify url: $url, real hash value: $real_version, expected value: $version_filename" 1>&2
                       exit 1
                    fi
                fi
            else
                real_version=$(get_url_version $url)
            fi

			VERSION=${real_version}
			local SRC_FILENAME=${WEB_CACHE_PATH}/${WEB_FILENAME}-${VERSION}.tgz
            SRC_FILENAMES[${DST_FILENAME}]=${SRC_FILENAME}

			[ -f ${BUILD_WEB_VERSION_FILE} ] && build_version=$(grep "^${url}==${real_version}" ${BUILD_WEB_VERSION_FILE} | awk -F"==" '{print $NF}')
			if [ -z ${build_version} ]; then
				echo "$url==$real_version" >> ${BUILD_WEB_VERSION_FILE}
				sort ${BUILD_WEB_VERSION_FILE} -o ${BUILD_WEB_VERSION_FILE} -u &> /dev/null
			fi
		fi
	done

    $REAL_COMMAND "${parameters[@]}"
    local result=$?

    #Return if there is any error
    if [ ${result} -ne 0 ]; then
        exit ${result}
    fi

    for filename in "${!filenames[@]}"
    do
        if [ -f "$filename" ] ; then
            mv "$filename" "${filenames[$filename]}"
        fi
    done

	if [[  -z "$(get_version_cache_option)" ]]; then
		return $result
	fi


	#Save them into cache
    for DST_FILENAME in "${!SRC_FILENAMES[@]}"
    do
		SRC_FILENAME=${SRC_FILENAMES[${DST_FILENAME}]}
        if [[ ! -e "${DST_FILENAME}" || -e ${SRC_FILENAME} ]] ; then
			continue
		fi
		FLOCK ${SRC_FILENAME}
		cp ${DST_FILENAME} ${SRC_FILENAME}
		chmod -f 777 ${SRC_FILENAME}
		FUNLOCK ${SRC_FILENAME}
		log_info "Saving into web cache URL:${url}, DST:${SRC_FILENAME}, SRC:${DST_FILENAME}"
	done

    return $result
}

run_pip_command()
{
    parameters=("$@")
    PIP_CACHE_PATH=${PKG_CACHE_PATH}/pip
    PKG_CACHE_OPTION="--cache-dir=${PIP_CACHE_PATH}"

    if [ ! -x "$REAL_COMMAND" ] && [ " $1" == "freeze" ]; then
        return 1
    fi

    if [[ "$SKIP_BUILD_HOOK" == Y || "$ENABLE_VERSION_CONTROL_PY" != "y" ]]; then
		if [ ! -z "$(get_version_cache_option)" ]; then
			mkdir -p ${PIP_CACHE_PATH}
			FLOCK ${PIP_CACHE_PATH}
			$REAL_COMMAND ${PKG_CACHE_OPTION} "$@"
			local result=$?
			chmod -f -R 777 ${PIP_CACHE_PATH}
 			touch ${PIP_CACHE_PATH}
			FUNLOCK ${PIP_CACHE_PATH}
			return ${result}
		fi
		$REAL_COMMAND "$@"
		return $?
    fi

    local found=n
    local install=n
    local pip_version_file=$PIP_VERSION_FILE
    local tmp_version_file=$(mktemp)
    [ -f "$pip_version_file" ] && cp -f $pip_version_file $tmp_version_file
    for para in "${parameters[@]}"
    do
        ([ "$para" == "-c" ] || [ "$para" == "--constraint" ]) && found=y
        if [ "$para" == "install" ]; then
            install=y
        elif [[ "$para" == *.whl ]]; then
            package_name=$(echo $para | cut -d- -f1 | tr _ .)
            $SUDO sed "/^${package_name}==/d" -i $tmp_version_file
        elif [[ "$para" == *==* ]]; then
            # fix pip package constraint conflict issue
            package_name=$(echo $para | cut -d= -f1)
            $SUDO sed "/^${package_name}==/d" -i $tmp_version_file
        fi
    done

    if [ "$found" == "n" ] && [ "$install" == "y" ]; then
        parameters+=("-c")
        parameters+=("${tmp_version_file}")
    fi

    if [ ! -z "$(get_version_cache_option)" ]; then
        FLOCK ${PIP_CACHE_PATH}
        $REAL_COMMAND ${PKG_CACHE_OPTION} "${parameters[@]}"
        local result=$?
        chmod -f -R 777 ${PIP_CACHE_PATH}
        touch ${PIP_CACHE_PATH}
        FUNLOCK ${PIP_CACHE_PATH}
    else
        $REAL_COMMAND "${parameters[@]}"
        local result=$?
    fi

    rm $tmp_version_file
    return $result
}

# Note:  set -x yields trace output that causes the module test failures.

run_python_command()
{
    parameters=("$@")

    if [ ! -x "$REAL_COMMAND" ] && [ " $1" == "freeze" ]; then
        return 1
    fi
    
	if [[  $1 != "setup.py" || $2 != "bdist_wheel" || "${SKIP_BUILD_HOOK}" == Y || "${ENABLE_VERSION_CONTROL_PY}" != "y" ]]; then
		$REAL_COMMAND "$@"
		local result=$?
		return ${result}
	fi

    PYTHON_CACHE_PATH=${PKG_CACHE_PATH}/python/
	PYTHON_FILE=${PWD}/setup.py
	if [ -e ${PYTHON_FILE} ]; then 
		SHAVAL=$(cat ${PYTHON_FILE} | sha1sum | awk '{print substr($1,0,11);}' )
	fi
	PYTHON_CACHE_FILE=${PYTHON_CACHE_PATH}/$(basename ${PWD})-${SHAVAL}.tgz


	# Load the .eggs from version cache if exists already
	if [[  -e ${PYTHON_FILE} && ! -z "$(get_version_cache_option)" && -e ${PYTHON_CACHE_FILE} ]]; then
		FLOCK ${PYTHON_CACHE_FILE}
		tar -C ${PWD} -zxvf  ${PYTHON_CACHE_FILE}
		FUNLOCK ${PYTHON_CACHE_FILE}
	fi

	# Run the real python command
	$REAL_COMMAND "$@"
	local result=$?

	# Save the .eggs into version cache
	if [[  -e ${PYTHON_FILE} && ! -z "$(get_version_cache_option)"  ]]; then
		mkdir -p ${PYTHON_CACHE_PATH}
		chmod -f 777 ${PYTHON_CACHE_PATH}
		FLOCK ${PYTHON_CACHE_FILE}
		tar -C ${PWD} -zcvf ${PYTHON_CACHE_FILE} .eggs
		chmod -f 777 ${PYTHON_CACHE_FILE}
		FUNLOCK ${PYTHON_CACHE_FILE}
	fi

	return ${result}
}

# Check if the command is to install the debian packages
# The apt/apt-get command format: apt/apt-get [options] {update|install}
check_apt_install()
{
    for para in "$@"
    do
        if [[ "$para" == -* ]]; then
            continue
        fi

        if [[ "$para" == "install"  ]]; then
            echo y
        fi

        break
    done
}

# Print warning message if a debian package version not specified when debian version control enabled.
check_apt_version()
{
    VERSION_FILE="${VERSION_PATH}/versions-deb"
    local install=$(check_apt_install "$@")
    if [ "$ENABLE_VERSION_CONTROL_DEB" == "y" ] && [ "$install" == "y" ]; then
        for para in "$@"
        do
            if [[ "$para" == -* ]]; then
                continue
            fi

            if [ "$para" == "install" ]; then
                continue
            fi

            if [[ "$para" == *=* ]]; then
                continue
            else
                package=$para
                if ! grep -q "^${package}=" $VERSION_FILE; then
                    echo "Warning: the version of the package ${package} is not specified." 1>&2
                fi
            fi
        done
    fi
}

acquire_apt_installation_lock()
{
    local result=n
    local wait_in_second=10
    local count=60
    local info="$1"
    for ((i=1; i<=$count; i++)); do
        if [ -f $DPKG_INSTALLTION_LOCK_FILE ]; then
            local lock_info=$(cat $DPKG_INSTALLTION_LOCK_FILE || true)
            echo "Waiting dpkg lock for $wait_in_second, $i/$count, info: $lock_info" 1>&2
            sleep $wait_in_second
        else
            # Create file in an atomic operation
            if (set -o noclobber; echo "$info">$DPKG_INSTALLTION_LOCK_FILE) &>/dev/null; then
                result=y
                break
            else
                echo "Failed to creat lock, Waiting dpkg lock for $wait_in_second, $i/$count, info: $lock_info" 1>&2
                sleep $wait_in_second
            fi
        fi
    done

    echo $result
}

release_apt_installation_lock()
{
    rm -f $DPKG_INSTALLTION_LOCK_FILE
}

ENABLE_VERSION_CONTROL_DEB=$(check_version_control "deb")
ENABLE_VERSION_CONTROL_PY2=$(check_version_control "py2")
ENABLE_VERSION_CONTROL_PY3=$(check_version_control "py3")
ENABLE_VERSION_CONTROL_WEB=$(check_version_control "web")
ENABLE_VERSION_CONTROL_GIT=$(check_version_control "git")
ENABLE_VERSION_CONTROL_PYTHON=$(check_version_control "python")
ENABLE_VERSION_CONTROL_GO=$(check_version_control "go")
ENABLE_VERSION_CONTROL_DOCKER=$(check_version_control "docker")

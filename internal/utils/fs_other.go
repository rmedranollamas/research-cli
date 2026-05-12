//go:build !unix

package utils

import (
	"fmt"
	"os"
)

func openOutputFile(path string, force bool) (*os.File, error) {
	if force {
		info, err := os.Lstat(path)
		if err != nil && !os.IsNotExist(err) {
			return nil, err
		}
		if err == nil && info.Mode()&os.ModeSymlink != 0 {
			return nil, fmt.Errorf("output file %s is a symlink; refusing to overwrite", SanitizePath(path))
		}
	}

	flags := os.O_WRONLY | os.O_CREATE
	if force {
		flags |= os.O_TRUNC
	} else {
		flags |= os.O_EXCL
	}

	return os.OpenFile(path, flags, 0644)
}

//go:build !unix

package utils

import (
	"fmt"
	"os"
)

func openOutputFile(path string, force bool) (*os.File, error) {
	if force {
		infoPre, err := os.Lstat(path)
		if err != nil && !os.IsNotExist(err) {
			return nil, err
		}
		if err == nil && infoPre.Mode()&os.ModeSymlink != 0 {
			return nil, fmt.Errorf("output file %s is a symlink; refusing to overwrite", SanitizePath(path))
		}
	}

	flags := os.O_WRONLY | os.O_CREATE
	if !force {
		flags |= os.O_EXCL
	}

	f, err := os.OpenFile(path, flags, 0644)
	if err != nil {
		return nil, err
	}

	if force {
		infoPost, err := os.Lstat(path)
		if err != nil {
			f.Close()
			return nil, err
		}
		if infoPost.Mode()&os.ModeSymlink != 0 {
			f.Close()
			return nil, fmt.Errorf("output file %s is a symlink; refusing to overwrite", SanitizePath(path))
		}

		infoF, err := f.Stat()
		if err != nil {
			f.Close()
			return nil, err
		}

		if !os.SameFile(infoF, infoPost) {
			f.Close()
			return nil, fmt.Errorf("output file %s was replaced during open; refusing to overwrite", SanitizePath(path))
		}

		if err := f.Truncate(0); err != nil {
			f.Close()
			return nil, err
		}
	}

	return f, nil
}

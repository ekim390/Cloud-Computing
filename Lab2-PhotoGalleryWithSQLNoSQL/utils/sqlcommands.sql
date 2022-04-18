CREATE TABLE `User` (
  `userID` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL, 
  `firstName` TEXT NOT NULL, 
  `lastName` TEXT NOT NULL, 
  `password` TEXT NOT NULL,
  `createdAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `token` TEXT NOT NULL,
  `confirmed` BOOLEAN NOT NULL,
  PRIMARY KEY (`email`)
);

CREATE TABLE `Album` (
  `albumID` varchar(100) NOT NULL,
  `name` TEXT NOT NULL,
  `description` TEXT NOT NULL,
  `thumbnailURL` TEXT NOT NULL,
  `createdAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `creator` varchar(100) NOT NULL,
  PRIMARY KEY (`albumID`),
  FOREIGN KEY (`creator`) REFERENCES `User` (`email`) ON DELETE CASCADE
);

CREATE TABLE `Photo` (
  `photoID` varchar(100) NOT NULL,
  `albumID` varchar(100) NOT NULL,
  `title` TEXT,
  `description` TEXT,
  `tags` TEXT,
  `photoURL` TEXT NOT NULL,
  `EXIF` TEXT,
  `createdAt` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updatedAt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`photoID`),
  FOREIGN KEY (`albumID`) REFERENCES `Album` (`albumID`) ON DELETE CASCADE ON UPDATE CASCADE
);